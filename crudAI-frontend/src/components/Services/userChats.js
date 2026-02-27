import axios from "axios";

export const userChats = async () => {
    const userId = localStorage.getItem('user_id');
    if(!userId) return []

    const res = await axios.get(`http://127.0.0.1:8000/users/${userId}/chats`)
    return res.data
}