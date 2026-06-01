import { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import TopBar from "./components/TopBar";
import Feed from "./pages/Feed";
import UsersPage from "./pages/UsersPage";
import UserPostsPage from "./pages/UserPostsPage";
import MyProfilePage from "./pages/MyProfilePage";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import NewPost from "./pages/NewPost";
import About from "./pages/About";

function App() {
  const [currentUser, setCurrentUser] = useState(null);

  // On first load, ask the backend if we are already logged in
  useEffect(() => {
    fetch('/api/me', { credentials: 'include' })
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data) setCurrentUser(data); });
  }, []);

  return (
    <div style={{ padding: '20px' }}>
      <TopBar currentUser={currentUser} setCurrentUser={setCurrentUser} />

      <Routes>
        <Route path="/Home" element={<Feed currentUser={currentUser} />} />
        <Route path="/Users" element={<UsersPage />} />
        <Route path="/user-posts/:userId" element={<UserPostsPage currentUser={currentUser} />} />
        <Route
          path="/profile"
          element={currentUser ? <MyProfilePage currentUser={currentUser} /> : <Navigate to="/Login" />}
        />
        <Route path="/Login" element={<Login setCurrentUser={setCurrentUser} />} />
        <Route path="/Signup" element={<Signup />} />
        <Route
          path="/new-post"
          element={currentUser ? <NewPost /> : <Navigate to="/Login" />}
        />
        <Route path="/About" element={<About />} />
        <Route path="/" element={<Navigate to="/Home" />} />
      </Routes>
    </div>
  );
}

export default App;
