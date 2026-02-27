import "./App.css";
import Navbar from "./components/Navbar/Navbar";
import Main from "./components/Main/Main";
import Sidebar from "./components/Sidebar/Sidebar";
import { useUserSetup } from "./components/Services/useUserSetup";
import { useState } from "react";
import axios from "axios";
import Offcanvas from "./components/SourcesOffcanvas/Offcanvas";
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

function App() {
  const { isLoggedIn, userName, userId } = useUserSetup();
  const [messages, setMessages] = useState([]);
  const [activeThread, setActiveThread] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sources, setSources] = useState([]);

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };
  // get chat history for each chat
  const handleChatClick = async (thread_id) => {
    try {
      const res = await axios.get(
        `http://127.0.0.1:8000/users/chats/${thread_id}/messages`,
      );
      setActiveThread(thread_id);
      const mapped = res.data.map((msg) => ({
        ...msg, message_id: msg.id
      }))
      setMessages(mapped);
    } catch (error) {
      console.log(error);
    }
  };
  return (
    <>
      <Navbar />
      <Sidebar
        isLoggedIn={isLoggedIn}
        user={userName}
        handleChatClick={handleChatClick}
      />
      <Main
        messages={messages}
        setMessages={setMessages}
        activeThread={activeThread}
        setActiveThread={setActiveThread}
        userId={userId}
        toggleSidebar={toggleSidebar}
        setSources={setSources}
        sidebarOpen = {sidebarOpen}
      />
      <Offcanvas
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        sources={sources}
      />
      <ToastContainer position="bottom-center" autoClose={3000} theme="dark"/>
    </>
  );
}

export default App;
