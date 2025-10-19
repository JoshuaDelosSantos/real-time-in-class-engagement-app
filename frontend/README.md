# Frontend

Web client for ClassEngage built with vanilla HTML, CSS, and JavaScript.

## Structure

```
frontend/
├── public/           # Static assets served by FastAPI
│   ├── index.html    # Home page
│   ├── session.html  # Session detail page
│   ├── css/
│   │   └── styles.css     # Application styles
│   └── js/
│       ├── utils.js       # Helper functions (escapeHtml, etc.)
│       ├── components.js  # Reusable form builders
│       ├── api.js         # API layer (fetch wrappers)
│       ├── ui.js          # Home page logic & event handlers
│       └── session.js     # Session page logic & rendering
└── README.md         # This file
```

## Development

The frontend is served by FastAPI from `public/`. No build step required.

**Running locally:**

```bash
cd infra/
docker compose up
# Visit http://localhost:8000
```

## Architecture

- **Separation of concerns:** HTML, CSS, and JavaScript are in separate files
- **Modular JavaScript:** Utilities, API calls, and UI logic are split into focused modules
- **Vanilla stack:** No frameworks or build tools; easy for new contributors to understand
- **Future-ready:** Structure supports migration to React/Vue/Svelte when needed

## Key Files

- `public/index.html` - Home page with create/join forms
- `public/session.html` - Session detail page with participant roster and questions
- `public/css/styles.css` - All application styles (layout, components, session page, utilities)
- `public/js/utils.js` - Pure functions (HTML escaping, etc.)
- `public/js/components.js` - Reusable form builders
- `public/js/api.js` - Centralised API communication (session creation, join, details, participants, questions)
- `public/js/ui.js` - Home page event handlers and DOM rendering
- `public/js/session.js` - Session page rendering, filtering, and parallel data loading

## Developer Guide

See `docs/frontend-guide.md` for:
- Fetch API patterns
- Error handling
- Security (XSS prevention)
- Loading states
- CORS considerations

## Future Plans

- Introduce a component library (React/Vue) when complexity justifies it
- Add a build system (Vite/Webpack) for bundling and optimization
- Implement routing for multi-page navigation
- Add state management as features grow
