
export const getUserProfile = async (userId) => {
  const response = await fetch(`/api/users/${userId}/profile`, { credentials: 'include' });
  if (!response.ok) throw new Error("Failed to fetch profile");
  return response.json();
};

export const getMe = async () => {
  const response = await fetch('/api/me', { credentials: 'include' });
  if (!response.ok) throw new Error("Not logged in");
  return response.json();
};

export const updateMyBio = async (bio) => {
  const response = await fetch('/api/me/bio', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ bio }),
  });
  if (!response.ok) throw new Error("Failed to update bio");
  return response.json();
};

export const getFollowers = async (userId) => {
  const response = await fetch(`/api/users/${userId}/followers`, { credentials: 'include' });
  if (!response.ok) throw new Error("Failed to fetch followers");
  return response.json();
};

export const getFollowing = async (userId) => {
  const response = await fetch(`/api/users/${userId}/following`, { credentials: 'include' });
  if (!response.ok) throw new Error("Failed to fetch following");
  return response.json();
};

export const followUser = async (userId) => {
  const response = await fetch(`/api/users/${userId}/follow`, { method: 'POST', credentials: 'include' });
  return response.json();
};

export const unfollowUser = async (userId) => {
  const response = await fetch(`/api/users/${userId}/unfollow`, { method: 'POST', credentials: 'include' });
  return response.json();
};



export const fetchUsersWithPostCounts = () => {
  return fetch('/api/users', { credentials: 'include' })
    .then(r => r.json());
};

export const fetchPostsByUserId = (userId) => {
  return fetch(`/api/user-posts/${userId}`, { credentials: 'include' })
    .then(r => r.json())
    .then(data => ({ userName: data.user_name, posts: data.posts }));
};

export const fetchPostsAndUsers = (index) => {
  return Promise.all([
    fetch(`https://jsonplaceholder.typicode.com/posts?count=10&index=${index}`),
    fetch(`https://jsonplaceholder.typicode.com/users`)
  ])
    .then(responses => Promise.all(responses.map(r => r.json())))
    .then(([posts, users]) => {
      return posts.slice(index, index + 10).map(post => {
        const user = users.find(u => u.id === post.userId);
        return {
          title: post.title,
          email: user ? user.email : 'unknown@example.com',
          body: post.body
        };
      });
    });
};