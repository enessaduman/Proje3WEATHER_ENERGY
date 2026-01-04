from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import uvicorn
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/enerji-verisi")
def veri_gonder():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, 'energy_data_v2 [2].db')

    if not os.path.exists(db_path):
        return {"error": "Veritabanı dosyası bulunamadı."}

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # --- GÜNEŞ VERİSİ ---
        cursor.execute("SELECT full_date, expected_best, expected_worst, total_hourly_real FROM solar_energy_stats")
        solar_rows = cursor.fetchall()
        
        # --- RÜZGAR VERİSİ --- (Tablo ismini rüzgar tablonla eşleştir)
        cursor.execute("SELECT full_date, expected_best, expected_worst, total_hourly_real FROM wind_energy_stats")
        wind_rows = cursor.fetchall()
        
        conn.close()

        # Veriyi paketliyoruz
        return {
            "solar": [dict(row) for row in solar_rows],
            "wind": [dict(row) for row in wind_rows]
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)