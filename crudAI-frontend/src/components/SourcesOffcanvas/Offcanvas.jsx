import "./Offcanvas.css";

const Offcanvas = ({ sidebarOpen, setSidebarOpen, sources }) => {
  return (
    <div className={`sidebar ${sidebarOpen ? "open" : ""}`}>
      <div className="offcanvas-header">
        <h5 className="offcanvas-title" id="offcanvasScrollingLabel">
          Sources
        </h5>
        <button
          type="button"
          className="btn-close"
          onClick={() => setSidebarOpen(false)}
        />
      </div>
      <div className="sources-body">
        {sources.length === 0 ? (
          <p>No Sources Available</p>
        ) : (
          sources.map((source, index) => {
            const gethostname = () => {
              try {
                return new URL(source.url).hostname;
              } catch (error) {
                return source.url;
              }
            };
            const hostname = gethostname()
            const favicon = `https://www.google.com/s2/favicons?domain=${hostname}&sz=32`;
            return (
              <a
                href={source.url}
                target="_blank"
                className="source-card"
                key={index}
              >
                <div className="source-card-top">
                  <img src={favicon} className="source-favicon" />
                  <span className="source-hostname">{hostname}</span>{" "}
                </div>
                <p className="source-title">{source.title}</p>{" "}
              </a>
            );
          })
        )}
      </div>
    </div>
  );
};

export default Offcanvas;
