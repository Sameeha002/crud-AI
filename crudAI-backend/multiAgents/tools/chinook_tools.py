from .chinook_db import get_session, get_classes
from langchain_core.tools import tool

@tool
def get_albums_by_artist(artist: str):
    """Get all albums by an artist from the music database."""
    session = get_session()
    try:
        classes = get_classes()
        Artist = classes.Artist
        Album = classes.Album

        results = (
            session.query(Album.Title, Artist.Name)
            .join(Artist, Album.ArtistId == Artist.ArtistId)
            .filter(Artist.Name.ilike(f"%{artist}%"))
        )
        if not results:
            return f"No albums found for artist: {artist}"

        return [{"Album": r.Title, "Artist": r.Name} for r in results]
    finally:
        session.close()

@tool
def get_tracks_by_artist(artist: str):
    """Get all tracks/songs by an artist from the music database."""
    session = get_session()

    try:
        classes = get_classes()
        Artist = classes.Artist
        Album = classes.Album
        Track = classes.Track

        results  = (
            session.query(Track.Name, Artist.Name)
            .join(Artist, Album.ArtistId == Artist.ArtistId )
            .join(Track, Track.AlbumId == Album.AlbumId )
            .filter(Artist.Name.ilike(f"%{artist}%"))
            .all()
        )
        if not results:
            return f"No tracks found for artist: {artist}"

        return [{"Track": r[0], "Artist": r[1]} for r in results]
    finally:
        session.close()


@tool
def get_tracks_by_genre(genre: str):
    """Get all tracks belonging to a specific music genre."""
    session = get_session()
    try:
        classes = get_classes()
        Track = classes.Track
        Genre = classes.Genre
        Album = classes.Album
        Artist = classes.Artist

        results = (
            session.query(Track.Name, Artist.Name, Genre.Name)
            .join(Album, Track.AlbumId == Album.AlbumId)
            .join(Artist, Album.ArtistId == Artist.ArtistId)
            .join(Genre, Track.GenreId == Genre.GenreId)
            .filter(Genre.Name.ilike(f"%{genre}%"))
            .limit(20)
            .all()
        )

        if not results:
            return f"No tracks found for genre: {genre}"

        return [{"Track": r[0], "Artist": r[1], "Genre": r[2]} for r in results]
    finally:
        session.close()


@tool
def check_for_songs(song_title: str):
    """Check if a song exists in the database by its title."""
    session = get_session()
    try:
        classes = get_classes()
        Track = classes.Track
        Album = classes.Album
        Artist = classes.Artist

        results = (
            session.query(Track.Name, Artist.Name, Album.Title)
            .join(Album, Track.AlbumId == Album.AlbumId)
            .join(Artist, Album.ArtistId == Artist.ArtistId)
            .filter(Track.Name.ilike(f"%{song_title}%"))
            .all()
        )

        if not results:
            return f"No songs found with title: {song_title}"

        return [{"Track": r[0], "Artist": r[1], "Album": r[2]} for r in results]
    finally:
        session.close()

music_tools = [get_albums_by_artist, get_tracks_by_artist, get_tracks_by_genre, check_for_songs]


@tool
def get_invoices_by_customer_sorted_by_date(customer_id: str) -> list[dict]:
    """
    Get all invoices for a customer sorted by date descending.
    Useful when customer wants to see most recent or oldest invoices,
    or invoices within a specific date range.
    
    Args:
        customer_id (str): The customer ID to look up invoices for.
    
    Returns:
        list[dict]: List of invoices sorted by date descending.
    """
    session = get_session()
    try:
        classes = get_classes()
        Invoice = classes.Invoice

        results = (
            session.query(
                Invoice.InvoiceId,
                Invoice.CustomerId,
                Invoice.InvoiceDate,
                Invoice.BillingAddress,
                Invoice.BillingCountry,
                Invoice.Total
            )
            .filter(Invoice.CustomerId == int(customer_id))
            .order_by(Invoice.InvoiceDate.desc())
            .all()
        )

        if not results:
            return f"No invoices found for customer ID: {customer_id}"

        return [
            {
                "InvoiceId": r.InvoiceId,
                "CustomerId": r.CustomerId,
                "InvoiceDate": str(r.InvoiceDate),
                "BillingAddress": r.BillingAddress,
                "BillingCountry": r.BillingCountry,
                "Total": round(r.Total, 2)
            }
            for r in results
        ]
    finally:
        session.close()


@tool
def get_invoices_sorted_by_unit_price(customer_id: str) -> list[dict]:
    """
    Get all invoices for a customer sorted by total price from highest to lowest.
    Useful when customer wants to find invoices based on cost.
    
    Args:
        customer_id (str): The customer ID to look up invoices for.
    
    Returns:
        list[dict]: List of invoices sorted by total descending.
    """
    session = get_session()
    try:
        classes = get_classes()
        Invoice = classes.Invoice

        results = (
            session.query(
                Invoice.InvoiceId,
                Invoice.InvoiceDate,
                Invoice.Total
            )
            .filter(Invoice.CustomerId == int(customer_id))
            .order_by(Invoice.Total.desc())
            .all()
        )

        if not results:
            return f"No invoices found for customer ID: {customer_id}"

        return [
            {
                "InvoiceId": r.InvoiceId,
                "InvoiceDate": str(r.InvoiceDate),
                "Total": round(r.Total, 2)
            }
            for r in results
        ]
    finally:
        session.close()


@tool
def get_employee_by_invoice_and_customer(invoice_id: str, customer_id: str) -> dict:
    """
    Get the support employee associated with a specific invoice and customer.
    Useful when customer wants to know which employee handled their invoice.
    
    Args:
        invoice_id (str): The invoice ID.
        customer_id (str): The customer ID.
    
    Returns:
        dict: Employee name, title and email associated with the invoice.
    """
    session = get_session()

    try:
        invoice_id_int = int(invoice_id)
        customer_id_int = int(customer_id)
    except ValueError:
        return "Please provide valid numeric IDs for both invoice_id and customer_id. For example: invoice_id='5', customer_id='3'"

    session = get_session()
    try:
        classes = get_classes()
        Employee = classes.Employee
        Customer = classes.Customer
        Invoice = classes.Invoice

        result = (
            session.query(
                Employee.FirstName,
                Employee.LastName,
                Employee.Title,
                Employee.Email
            )
            .join(Customer, Customer.SupportRepId == Employee.EmployeeId)
            .join(Invoice, Invoice.CustomerId == Customer.CustomerId)
            .filter(
                Invoice.InvoiceId == int(invoice_id_int),
                Invoice.CustomerId == int(customer_id_int)
            )
            .first()
        )

        if not result:
            return f"No employee found for invoice ID {invoice_id} and customer ID {customer_id}."

        return {
            "EmployeeName": f"{result.FirstName} {result.LastName}",
            "Title": result.Title,
            "Email": result.Email
        }
    finally:
        session.close()


sales_tool = [get_employee_by_invoice_and_customer, get_invoices_by_customer_sorted_by_date, get_invoices_sorted_by_unit_price]