import axios from "axios";

export const userChats = async () => {
    const userId = localStorage.getItem('user_id');
    if(!userId) return []

    const res = await axios.get(`https://crud-ai.onrender.com/users/${userId}/chats`)
    return res.data
}