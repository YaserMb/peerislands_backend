from fastapi import FastAPI

app = FastAPI()

@app.get('/test')
def main():
    return 'yaser'