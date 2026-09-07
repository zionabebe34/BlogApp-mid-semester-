import { createTheme } from '@mui/material/styles';

// One place that defines the look of the whole blog:
// warm paper background, serif headings (classic editorial feel),
// ink-black buttons and a green accent — every page reads from this.
const serif = "Georgia, 'Times New Roman', serif";

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#1a1a1a' },   // ink black: buttons, tabs, emphasis
    secondary: { main: '#1a8917' }, // editorial green: accents & highlights
    background: { default: '#faf9f6', paper: '#ffffff' },
    text: { primary: '#242424', secondary: '#6b6b6b' },
    divider: '#e8e5de',
  },
  typography: {
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
    h1: { fontFamily: serif },
    h2: { fontFamily: serif },
    h3: { fontFamily: serif, fontWeight: 700 },
    h4: { fontFamily: serif, fontWeight: 700 },
    h5: { fontFamily: serif, fontWeight: 700 },
    h6: { fontFamily: serif, fontWeight: 700 },
    button: { textTransform: 'none', fontWeight: 600 },
  },
  shape: { borderRadius: 12 },
  components: {
    // Pill-shaped buttons everywhere
    MuiButton: {
      styleOverrides: { root: { borderRadius: 999 } },
    },
    // Cards get a soft border instead of a heavy shadow
    MuiCard: {
      styleOverrides: {
        root: {
          border: '1px solid #e8e5de',
          boxShadow: 'none',
        },
      },
    },
  },
});

export default theme;
