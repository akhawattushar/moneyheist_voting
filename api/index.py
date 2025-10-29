from app import app

# Vercel needs this
def handler(event, context):
    return app(event, context)
