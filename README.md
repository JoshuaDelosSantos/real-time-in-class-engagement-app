# ClassEngage
ClassEngage is a lightweight, real-time classroom engagement app (inspired by Kahoot) that helps teachers surface the most relevant student questions during live sessions.

## Overview
- **Audience**: One teacher hosts a session; 5–6 students join via a simple code.
- **Primary loop**: Students submit questions, classmates upvote, and teachers resolve the top-voted items.
- **Operating mode**: Near-real-time updates are sufficient—sub-second accuracy is not required.
- **Scale expectations**: ~20 concurrent users across multiple sessions.

## Current Feature Set
- Teacher starts a session and shares an auto-generated join code.
- Students join via the code.
- Students post questions and see the list update in real time.
- Upvotes bubble the most relevant questions to the top of the teacher dashboard.
- Teacher can mark questions as answered to close the loop.

## Near-Term Roadmap
- Add live polls, quick quizzes, and lightweight leaderboards.
- Capture basic engagement analytics per session for teacher review.
- Explore richer front-end interactivity with a modern JS framework once the core flows stabilize.

## Architecture Snapshot
- **Backend**: FastAPI serving REST endpoints and WebSocket channels.
- **Persistence**: PostgreSQL for durable session/question data.
- **Deployment target**: Dockerised services running on an Azure VM; optimized for low ops overhead.