import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Card, CardContent, Typography, TextField, Button } from '@mui/material';
import ReactQuill from 'react-quill-new';
import 'react-quill-new/dist/quill.snow.css';
import { createPost } from '../api';

// Toolbar config for the WYSIWYG editor: bold, italic, lists, and links.
const quillModules = {
  toolbar: [
    ['bold', 'italic', 'underline'],
    [{ list: 'ordered' }, { list: 'bullet' }],
    ['link'],
    ['clean'],
  ],
};

/**
 * "Write a story" page: title + optional cover image + rich-text body.
 * The body is sent to the backend as HTML produced by the Quill editor.
 */
function NewPost() {
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [imageFileName, setImageFileName] = useState('');
  const [error, setError] = useState('');

  const handlePublish = async (e) => {
    e.preventDefault();

    if (!title.trim()) {
      setError('Please enter a title for your post.');
      return;
    }
    // The editor returns HTML — strip the tags to check for real content
    const strippedBody = body.replace(/<[^>]*>/g, '').trim();
    if (!strippedBody) {
      setError('Please write some content for your post.');
      return;
    }

    try {
      await createPost(title, body, imageUrl);
      navigate('/Home');
    } catch (err) {
      setError('Failed to create post: ' + err.message);
    }
  };

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', mt: 5 }}>
      <Card sx={{ width: '100%', maxWidth: 700, p: 1 }}>
        <CardContent>
          <Typography variant="h4" sx={{ textAlign: 'center', mb: 4 }}>
            Write a story
          </Typography>

          {error && (
            <Typography color="error" sx={{ mb: 2, textAlign: 'center' }}>
              {error}
            </Typography>
          )}

          <form onSubmit={handlePublish}>
            <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>Title</Typography>
            <TextField
              fullWidth
              placeholder="Enter post title..."
              value={title}
              onChange={e => setTitle(e.target.value)}
              size="small"
              sx={{ mb: 3 }}
            />

            <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>Cover image (upload or URL)</Typography>
            <TextField
              fullWidth
              placeholder="https://example.com/photo.jpg"
              value={imageUrl}
              onChange={e => setImageUrl(e.target.value)}
              size="small"
              sx={{ mb: 1 }}
            />

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
              <Button
                variant="outlined"
                component="label"
                size="small"
              >
                Upload from device
                <input
                  type="file"
                  accept="image/*"
                  hidden
                  onChange={(e) => {
                    const file = e.target.files && e.target.files[0];
                    if (!file) return;
                    setImageFileName(file.name);
                    const reader = new FileReader();
                    reader.onload = () => {
                      setImageUrl(reader.result);
                    };
                    reader.readAsDataURL(file);
                  }}
                />
              </Button>
              {imageFileName && <Typography variant="caption">{imageFileName}</Typography>}
            </Box>

            {imageUrl && (
              <Box
                component="img"
                src={imageUrl}
                alt="preview"
                sx={{ width: '100%', maxHeight: 300, objectFit: 'cover', borderRadius: 2, mb: 3 }}
              />
            )}

            <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>Body</Typography>
            <Box sx={{ mb: 6 }}>
              <ReactQuill
                theme="snow"
                value={body}
                onChange={setBody}
                modules={quillModules}
                placeholder="Write your post content here..."
                style={{ height: 200 }}
              />
            </Box>

            <Button fullWidth type="submit" variant="contained" sx={{ py: 1.3, fontSize: 16 }}>
              Publish
            </Button>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
}

export default NewPost;
