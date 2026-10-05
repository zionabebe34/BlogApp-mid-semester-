import { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import { getMe } from './api';
import TopBar from './components/TopBar';
import Feed from './pages/Feed';
import UsersPage from './pages/UsersPage';
import UserPostsPage from './pages/UserPostsPage';
import MyProfilePage from './pages/MyProfilePage';
import Login from './pages/Login';
import Signup from './pages/Signup';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import NewPost from './pages/NewPost';
import About from './pages/About';
import AdminPage from './pages/AdminPage';

/**
 * Root component. It does two jobs:
 *
 * 1. Holds `currentUser` (null = not logged in). On first load it asks the
 *    backend "who am I?" so a page refresh keeps you logged in. The value
 *    is passed down to pages that need it, and Login/TopBar update it.
 *
 * 2. Maps every URL to a page. Routes that need a login (profile, new post)
 *    redirect to /Login when there is no current user.
 */
function App() {
  const [currentUser, setCurrentUser] = useState(null);

  useEffect(() => {
    getMe()
      .then(setCurrentUser)
      .catch(() => setCurrentUser(null)); // not logged in — that's fine
  }, []);

  return (
    <>
      <TopBar currentUser={currentUser} setCurrentUser={setCurrentUser} />

      {/* Centered content column shared by every page */}
      <Box component="main" sx={{ maxWidth: 1100, mx: 'auto', px: { xs: 2, md: 3 }, pb: 10 }}>
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
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route
            path="/new-post"
            element={currentUser ? <NewPost /> : <Navigate to="/Login" />}
          />
          {/* Staff-only page. This guard is UX; the backend decorator is the real one. */}
          <Route
            path="/admin"
            element={
              currentUser && ['admin', 'moderator'].includes(currentUser.role)
                ? <AdminPage currentUser={currentUser} />
                : <Navigate to="/Home" />
            }
          />
          <Route path="/About" element={<About />} />
          <Route path="/" element={<Navigate to="/Home" />} />
        </Routes>
      </Box>
    </>
  );
}

export default App;
