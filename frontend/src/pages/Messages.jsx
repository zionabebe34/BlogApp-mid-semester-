import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box, Card, List, ListItemButton, ListItemAvatar, ListItemText, Avatar,
  Typography, TextField, Button, Badge,
} from '@mui/material';
import { getMe, getConversations, getMessages, sendMessage } from '../api';
import { timeAgo } from '../utils/timeAgo';

const POLL_INTERVAL_MS = 4000;

function Messages({ currentUser }) {
  const { userId } = useParams();
  const navigate = useNavigate();
  const [myId, setMyId] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [thread, setThread] = useState([]);
  const [draft, setDraft] = useState('');
  const bottomRef = useRef(null);

  const loadConversations = useCallback(() => {
    getConversations().then(setConversations).catch(() => {});
  }, []);

  const loadThread = useCallback(() => {
    if (!userId) return;
    getMessages(userId).then(setThread).catch(() => {});
  }, [userId]);

  useEffect(() => {
    if (!currentUser) {
      navigate('/Login');
      return;
    }
    getMe().then(me => setMyId(me.id));
    loadConversations();
  }, [currentUser, navigate, loadConversations]);

  useEffect(() => {
    loadThread();
  }, [loadThread]);

  // Poll for new messages while a thread is open
  useEffect(() => {
    if (!userId) return;
    const interval = setInterval(() => {
      loadThread();
      loadConversations();
    }, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [userId, loadThread, loadConversations]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [thread]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!draft.trim()) return;
    try {
      await sendMessage(userId, draft);
      setDraft('');
      loadThread();
      loadConversations();
    } catch (err) {
      alert(err.message);
    }
  };

  const activeConversation = conversations.find(c => String(c.user_id) === String(userId));

  return (
    <Box sx={{ display: 'flex', gap: 2, mt: 4, height: '70vh' }}>
      {/* Conversation list */}
      <Card sx={{ width: 280, overflowY: 'auto', flexShrink: 0 }}>
        <List sx={{ p: 0 }}>
          {conversations.length === 0 && (
            <Typography sx={{ p: 2, color: 'text.secondary' }}>No conversations yet.</Typography>
          )}
          {conversations.map(c => (
            <ListItemButton
              key={c.user_id}
              selected={String(c.user_id) === String(userId)}
              onClick={() => navigate(`/messages/${c.user_id}`)}
            >
              <ListItemAvatar>
                <Badge badgeContent={c.unread_count} color="secondary" invisible={!c.unread_count}>
                  <Avatar src={c.profile_picture_url} alt={c.name} />
                </Badge>
              </ListItemAvatar>
              <ListItemText primary={c.name} secondary={c.last_message} />
            </ListItemButton>
          ))}
        </List>
      </Card>

      {/* Thread */}
      <Card sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        {!userId ? (
          <Box sx={{ m: 'auto', color: 'text.secondary' }}>Select a conversation</Box>
        ) : (
          <>
            <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
              <Typography variant="h6">{activeConversation?.name || 'Conversation'}</Typography>
            </Box>
            <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 2 }}>
              {thread.map(m => (
                <Box
                  key={m.id}
                  sx={{
                    display: 'flex',
                    justifyContent: m.sender_id === myId ? 'flex-end' : 'flex-start',
                    mb: 1,
                  }}
                >
                  <Box
                    sx={{
                      bgcolor: m.sender_id === myId ? 'primary.main' : 'action.hover',
                      color: m.sender_id === myId ? 'primary.contrastText' : 'text.primary',
                      borderRadius: 2,
                      px: 1.5,
                      py: 0.75,
                      maxWidth: '70%',
                    }}
                  >
                    <Typography variant="body2">{m.content}</Typography>
                    <Typography variant="caption" sx={{ opacity: 0.7 }}>
                      {timeAgo(m.created_at)}
                    </Typography>
                  </Box>
                </Box>
              ))}
              <div ref={bottomRef} />
            </Box>
            <Box
              component="form"
              onSubmit={handleSend}
              sx={{ p: 2, display: 'flex', gap: 1, borderTop: '1px solid', borderColor: 'divider' }}
            >
              <TextField
                fullWidth
                size="small"
                placeholder="Type a message…"
                value={draft}
                onChange={e => setDraft(e.target.value)}
              />
              <Button type="submit" variant="contained">Send</Button>
            </Box>
          </>
        )}
      </Card>
    </Box>
  );
}

export default Messages;
