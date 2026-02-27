import React from "react";
import "./Navbar.css";
import { BsLayoutSidebarInsetReverse } from "react-icons/bs";

const Navbar = () => {
  return (
    <nav className="navbar">
      <div className="container-fluid">
          
          
          <BsLayoutSidebarInsetReverse
          className="sidebar-icon"
          role="button"
          data-bs-toggle="offcanvas"
          data-bs-target="#offcanvasScrolling"
          aria-controls="offcanvasScrolling"
        />
        <h2 className="navbar-brand">CRUD AI</h2>
      </div>
    </nav>
  );
};

export default Navbar;
