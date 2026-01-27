import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

function AuthCallback() {
  const navigate = useNavigate();

  useEffect(() => {
    // 1️⃣ Always try to read token from URL hash FIRST
    const hash = window.location.hash;
    const params = new URLSearchParams(hash.substring(1));
    let idToken = params.get("id_token");

    // 2️⃣ If not in URL, fall back to stored token
    if (!idToken) {
      idToken = localStorage.getItem("id_token");
    }

    if (!idToken) {
      document.body.innerHTML = "<h3>Login failed</h3>";
      throw new Error("No token received");
    }

    // 3️⃣ Decode JWT
    const payload = JSON.parse(atob(idToken.split(".")[1]));
    console.log("Token payload:", payload);

    const groups = payload["cognito:groups"];

    // 4️⃣ Save / overwrite token (important!)
    localStorage.setItem("id_token", idToken);

    // 5️⃣ Redirect based on group (same logic)
    if (groups && groups.includes("Admin_auth")) {
      navigate("/admin");
    } else if (groups && groups.includes("Students_auth")) {
      navigate("/");
    } else {
      navigate("/user");
    }

  }, [navigate]);

  return <h2>Logging you in...</h2>;
}

export default AuthCallback;

