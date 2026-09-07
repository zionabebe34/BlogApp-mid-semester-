/*
 * All backend calls live in this one file, so pages and components never
 * use fetch() directly — they just call a named function from here.
 *
 * Every request includes `credentials: 'include'` so the session cookie
 * (set by the backend on login) travels with it. That cookie is how the
 * backend knows who is logged in.
 */

/**
 * Small wrapper around fetch:
 * - always sends the session cookie
 * - JSON-encodes the body when one is given
 * - throws an Error with the backend's message when the response is not OK
 */
async function request(path, { method = 'GET', body } = {}) {
  const response = await fetch(path, {
    method,
    credentials: 'include',
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(data?.message || data?.error || 'Request failed');
  }
  return data;
}

// ── Auth ─────────────────────────────────────────────────────────────────────

export const signup = (name, email, password) =>
  request('/api/signup', { method: 'POST', body: { name, email, password } });

export const login = (email, password) =>
  request('/api/login', { method: 'POST', body: { email, password } });

export const logout = () => request('/api/logout', { method: 'POST' });

/** Who is currently logged in? Throws if nobody is. */
export const getMe = () => request('/api/me');

// ── Profile ──────────────────────────────────────────────────────────────────

/** User details + follower counts + their posts, all in one response. */
export const getUserProfile = (userId) => request(`/api/users/${userId}/profile`);

export const updateMyBio = (bio) =>
  request('/api/me/bio', { method: 'PUT', body: { bio } });

// ── Posts & feeds ────────────────────────────────────────────────────────────

/** Global feed page: newest posts first, paginated. */
export const fetchGlobalFeed = (limit, offset) =>
  request(`/api/feed?limit=${limit}&offset=${offset}`);

/** Personal feed: posts only from people the logged-in user follows. */
export const fetchFollowingFeed = () => request('/api/feed/following');

export const createPost = (title, body, imageUrl) =>
  request('/api/new-post', {
    method: 'POST',
    body: { title, body, image_url: imageUrl || null },
  });

// ── Users ────────────────────────────────────────────────────────────────────

export const fetchUsersWithPostCounts = () => request('/api/users');

export const searchUsers = (query) =>
  request(`/api/users/search?q=${encodeURIComponent(query)}`);

// ── Social (follow / unfollow) ───────────────────────────────────────────────

export const followUser = (userId) =>
  request(`/api/users/${userId}/follow`, { method: 'POST' });

export const unfollowUser = (userId) =>
  request(`/api/users/${userId}/unfollow`, { method: 'POST' });

export const getFollowers = (userId) => request(`/api/users/${userId}/followers`);

export const getFollowing = (userId) => request(`/api/users/${userId}/following`);

// ── Social (like / unlike) ───────────────────────────────────────────────
export const likePost = (postId) =>
  request(`/api/posts/${postId}/like`, { method: 'POST' });

export const unlikePost = (postId) =>
  request(`/api/posts/${postId}/unlike`, { method: 'POST' });

export const getPostLikes = (postId) => request(`/api/posts/${postId}/likes`);

// ── Social (comments) ───────────────────────────────────────────────────────
// Note: these use the /api/user-posts/ prefix (not /api/posts/) to match the
// route names already defined in the backend.

export const getPostComments = (postId) =>
  request(`/api/user-posts/${postId}/comments`);

export const addComment = (postId, content) =>
  request(`/api/user-posts/${postId}/comments`, {
    method: 'POST',
    body: { content },
  });
