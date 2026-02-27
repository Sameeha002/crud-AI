import axios from "axios";
import { useEffect, useState } from "react";

export const useUserSetup = () => {
  const[userName, setUserName] = useState(null)
  const[isLoggedIn, setIsLoggedIn] = useState(false)
  const [userId, setUserId] = useState(null);

  useEffect(() => {

    const setupUser = async () => {
      try{
        const res = await axios.post(
        "http://127.0.0.1:8000/users/get-or-create",
        {name: "John", email: "john@gmail.com"});


        if(res.data?.id){
          localStorage.setItem("user_id", res.data.id)
          setUserId(res.data.id)
          setIsLoggedIn(true)
          setUserName(res.data)

      }
        } catch (err) {
          console.error("User setup failed", err)

        }

      
    };

    setupUser();

  }, []);

  return {
    userName,
    userId,
    isLoggedIn: !!userName,

  }
};
