# Environment Configuration

## Frontend Environment Variables

Create a `.env.local` file in the `frontend/auction-app` directory with the following variables:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# App Configuration  
NEXT_PUBLIC_APP_NAME="Auction Platform"
NEXT_PUBLIC_APP_DESCRIPTION="Real-time auction platform with microservices"
```

## Backend Environment Variables

The backend services can be configured with the following environment variables:

```bash
# JWT Configuration
JWT_SECRET=your-secret-key-change-in-production

# Database Configuration (optional, defaults to SQLite)
DATABASE_URL=sqlite:///./app.db
```

## Production Deployment

For production deployment, make sure to:

1. Change the `JWT_SECRET` to a strong, unique value
2. Update `NEXT_PUBLIC_API_URL` to your production API endpoint
3. Consider using a production database instead of SQLite
4. Enable HTTPS for all services
5. Set up proper CORS configuration 