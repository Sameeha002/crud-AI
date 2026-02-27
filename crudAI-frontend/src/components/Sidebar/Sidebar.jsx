import { useEffect, useState } from "react";
import "./Sidebar.css";
import axios from "axios";
import { userChats } from "../Services/userChats";


const Sidebar = ({isLoggedIn, user, handleChatClick}) => {
 
  const API_URL = 'http://127.0.0.1:8000/products'

  const [products, setProducts] = useState([])
  const [chats, setChats] = useState([])
  // get all chats for user

    useEffect(() => {
      const fetchChats = async() => {
        const userId = localStorage.getItem('user_id')
        if(!userId) return;


        const res = await userChats();
        console.log("Chats from backend:", res);
        setChats(res)

      }
      fetchChats()

    },[])


// get all products from api
  const handleSend = async() => {
    try {
      const response = await axios.get(API_URL)
      setProducts(response.data)
    } catch (error) {
      console.log(error)
    } 
  }
  
  // create a new chat
  const handleNewChat = async() => {
    try {
      const userId = localStorage.getItem('user_id')
      const res = await axios.post(
        "http://127.0.0.1:8000/users/create-chat",
        {
          user_id: userId,
          title: 'New Chat'
        }
      )
      setChats((prev) => [res.data, ...prev])
      handleChatClick(res.data.id)
    } catch (error) {
      console.log(error)
    }

  }

  return (
    <div
      className="offcanvas offcanvas-start"
      data-bs-scroll="true"
      data-bs-backdrop="false"
      tabIndex={-1}
      id="offcanvasScrolling"
      aria-labelledby="offcanvasScrollingLabel"
    >
      <div className="offcanvas-header">
        <h5 className="offcanvas-title" id="offcanvasScrollingLabel">
          CRUD AI
        </h5>
        <button
          type="button"
          className="btn-close"
          data-bs-dismiss="offcanvas"
        />
      </div>

      <div className="offcanvas-body">
        {
          isLoggedIn? (
            <p>Logged in as <b>{user.name}</b></p>
          ) : (
            <p> User is not logged In</p>

          )
        }
        <button className="new-chat" onClick={handleNewChat}>New Chat</button>
        <button className="get-products" onClick={handleSend}>Get All Products</button>
        
        {/* get all products */}
        <div className="get-prod-div">
          {products.map((prod) => (
            <ul key={prod.id} className="products">
              <li>{prod.title}, Rs. {prod.price}/-</li>
              
            </ul>
          ))}
        </div>

        

        {/* all chats */}
          <h5 className="your-chats">Your Chats</h5>
          {chats.map((chat) => {
            return <p key={chat.id} className="chat-title" onClick={() => handleChatClick(chat.id)}>{chat.title}</p>

          })}
      </div>
    </div>
  );
};



export default Sidebar;
