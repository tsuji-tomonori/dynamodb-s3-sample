from mangum import Mangum

from app import app

# Lambda用のハンドラー
handler = Mangum(app)
