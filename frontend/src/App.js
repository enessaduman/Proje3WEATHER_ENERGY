import React, { useState, useEffect, useMemo } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function App() {
  // State for energy data and UI controls
  const [solarData, setSolarData] = useState([]);
  const [windData, setWindData] = useState([]);
  const [activeType, setActiveType] = useState('genel');
  const [range, setRange] = useState([0, 168]);

  // Fetch energy data from the local API on component mount
  useEffect(() => {
    fetch('http://127.0.0.1:8001/enerji-verisi')
      .then(res => res.json())
      .then(resData => {
        if (resData.solar && resData.wind) {
          setSolarData(resData.solar);
          setWindData(resData.wind);
          setRange([0, Math.min(resData.solar.length - 1, 168)]);
        }
      })
      .catch(err => console.error("Database Connection Error:", err));
  }, []);

  // Determine which dataset to display based on the active mode
  const displayData = useMemo(() => {
    if (activeType === 'solar') return solarData;
    if (activeType === 'wind') return windData;

    return solarData.map((sItem, index) => {
      const wItem = windData[index];
      return {
        full_date: sItem.full_date || sItem.tarih,
        solar_real: sItem.total_hourly_real,
        wind_real: wItem ? wItem.total_hourly_real : 0
      };
    });
  }, [activeType, solarData, windData]);

  // Slice the dataset based on the slider selection
  const filteredData = useMemo(() => {
    if (!displayData.length) return [];
    return displayData.slice(range[0], Math.min(range[1] + 1, displayData.length));
  }, [displayData, range]);

  // Calculate percentage for slider label positioning
  const getPercent = (val) => (val / (displayData.length - 1 || 1)) * 100;

  const customStyles = `
    .range-slider-wrap { position: relative; width: 100%; height: 8px; background: #e0e0e0; border-radius: 5px; margin: 80px 0 40px 0; }
    .slider-active-bar { position: absolute; height: 100%; background: #2ecc71; border-radius: 5px; z-index: 2; }
    input[type="range"].range-input { position: absolute; width: 100%; top: -7px; pointer-events: none; appearance: none; background: none; z-index: 3; }
    input[type="range"].range-input::-webkit-slider-thumb { pointer-events: auto; appearance: none; width: 22px; height: 22px; border-radius: 50%; border: 3px solid white; cursor: pointer; box-shadow: 0 2px 6px rgba(0,0,0,0.2); }
    .start-thumb::-webkit-slider-thumb { background: #3498db; }
    .end-thumb::-webkit-slider-thumb { background: #e74c3c; }
    .label-start { position: absolute; top: -65px; transform: translateX(-50%); background: #3498db; color: white; padding: 5px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; white-space: nowrap; }
    .label-end { position: absolute; top: -35px; transform: translateX(-50%); background: #e74c3c; color: white; padding: 5px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; white-space: nowrap; }
    
    .guide-box { background: #f8f9fa; border-left: 4px solid #3498db; padding: 15px; margin-bottom: 20px; border-radius: 4px; }
    .guide-title { color: #2c3e50; font-weight: bold; margin-bottom: 5px; display: flex; align-items: center; gap: 8px; }
    
    .button-container { display: flex; justify-content: center; gap: 40px; margin-bottom: 50px; flex-wrap: wrap; }
    .wrapper-box { position: relative; width: 130px; height: 130px; display: flex; align-items: center; justify-content: center; }
    
    .sun-rays { position: absolute; width: 125px; height: 125px; background: repeating-conic-gradient(from 0deg, #FFD700 0deg 10deg, transparent 10deg 20deg); border-radius: 50%; opacity: ${activeType === 'solar' ? '1' : '0'}; transform: scale(1.15) rotate(10deg); transition: 0.5s; z-index: 1; -webkit-mask-image: radial-gradient(circle, white 38%, transparent 75%); }
    .wind-blades { position: absolute; width: 125px; height: 125px; background: conic-gradient(from 0deg, #3498db 0deg 40deg, transparent 40deg 120deg, #3498db 120deg 160deg, transparent 160deg 240deg, #3498db 240deg 280deg, transparent 280deg 360deg); border-radius: 50%; opacity: ${activeType === 'wind' ? '0.8' : '0'}; animation: spin 1.5s linear infinite; transition: 0.4s; z-index: 1; -webkit-mask-image: radial-gradient(circle, transparent 40%, white 41%, white 70%, transparent 71%); }
    .general-aura { position: absolute; width: 130px; height: 130px; border: 4px dotted #2ecc71; border-radius: 50%; opacity: ${activeType === 'genel' ? '1' : '0'}; animation: spin 8s linear infinite, pulse 2s ease-in-out infinite; transition: 0.5s; z-index: 1; }

    .main-btn { width: 95px; height: 95px; border-radius: 50%; cursor: pointer; border: 2px solid #eee; background: white; z-index: 2; display: flex; align-items: center; justify-content: center; text-align: center; font-weight: bold; font-size: 10px; transition: 0.3s; }
    .main-btn.active-solar { background: #FFD700; color: #2c3e50; border: none; box-shadow: 0 0 20px #FFD700; }
    .main-btn.active-wind { background: #3498db; color: white; border: none; box-shadow: 0 0 20px #3498db; }
    .main-btn.active-genel { background: #2ecc71; color: white; border: none; box-shadow: 0 0 20px #2ecc71; }

    @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    @keyframes pulse { 0% { transform: scale(1); opacity: 0.7; } 50% { transform: scale(1.08); opacity: 1; } 100% { transform: scale(1); opacity: 0.7; } }
  `;

  return (
    <div style={{ padding: '30px', fontFamily: 'Arial, sans-serif', backgroundColor: '#f4f7f9', minHeight: '100vh' }}>
      <style>{customStyles}</style>

      {/* HEADER SECTION */}
      <div style={{ textAlign: 'center', marginBottom: '40px' }}>
        <h1 style={{ color: '#2c3e50' }}>Smart Energy Insights</h1>
        {/* Project Description */}
        <p style={{ color: '#7f8c8d', maxWidth: '800px', margin: '10px auto', fontSize: '15px', lineHeight: '1.6' }}>
          Real-time Monitoring ✦ Predictive Analytics ✦ Solar & Wind ✦ Grid Management
        </p>
      </div>

      {/* TOOLTIP AND SLIDER SECTION */}
      <div style={{ backgroundColor: 'white', padding: '30px', borderRadius: '25px', boxShadow: '0 10px 25px rgba(0,0,0,0.05)', marginBottom: '35px' }}>
        <div className="guide-box">
          <div className="guide-title"><span>📅</span> Time Range Selector</div>
          <p style={{ fontSize: '13px', color: '#5f6c7b', lineHeight: '1.6' }}>
            Use the interactive slider below to focus on specific time periods.
            The <strong>blue handle</strong> marks the start of your analysis, while the <strong>red handle</strong> sets the end point.
            Adjusting these handles allows you to zoom in on daily peaks, nightly drops, or weekly performance trends.
          </p>
        </div>

        <div className="range-slider-wrap">
          <div className="slider-active-bar" style={{ left: `${getPercent(range[0])}%`, width: `${getPercent(range[1]) - getPercent(range[0])}%` }}></div>
          {displayData[range[0]] && (
            <div className="label-start" style={{ left: `${getPercent(range[0])}%` }}>
              {(displayData[range[0]].tarih || displayData[range[0]].full_date)?.substring(0, 16)}
            </div>
          )}
          <input type="range" min="0" max={displayData.length - 1 || 0} value={range[0]} className="range-input start-thumb"
            onChange={(e) => setRange([Math.min(parseInt(e.target.value), range[1] - 1), range[1]])} />
          {displayData[range[1]] && (
            <div className="label-end" style={{ left: `${getPercent(range[1])}%` }}>
              {(displayData[range[1]].tarih || displayData[range[1]].full_date)?.substring(0, 16)}
            </div>
          )}
          <input type="range" min="0" max={displayData.length - 1 || 0} value={range[1]} className="range-input end-thumb"
            onChange={(e) => setRange([range[0], Math.max(parseInt(e.target.value), range[0] + 1)])} />
        </div>
        <div style={{ textAlign: 'center', marginTop: '10px', fontSize: '12px', color: '#94a3b8' }}>
          <span style={{ color: '#3498db', fontWeight: 'bold' }}>●</span> Blue: Start Time | <span style={{ color: '#e74c3c', fontWeight: 'bold' }}>●</span> Red: End Time
        </div>
      </div>

      <div className="button-container">
        <div className="wrapper-box"><div className="sun-rays"></div><button onClick={() => setActiveType('solar')} className={`main-btn ${activeType === 'solar' ? 'active-solar' : ''}`}>SOLAR MODE</button></div>
        <div className="wrapper-box"><div className="general-aura"></div><button onClick={() => setActiveType('genel')} className={`main-btn ${activeType === 'genel' ? 'active-genel' : ''}`}>GENERAL OVERVIEW</button></div>
        <div className="wrapper-box"><div className="wind-blades"></div><button onClick={() => setActiveType('wind')} className={`main-btn ${activeType === 'wind' ? 'active-wind' : ''}`}>WIND MODE</button></div>
      </div>

      <div style={{ width: '100%', height: '500px', backgroundColor: 'white', padding: '30px', borderRadius: '30px', boxShadow: '0 15px 40px rgba(0,0,0,0.08)' }}>
        <ResponsiveContainer>
          <AreaChart data={filteredData}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
            <XAxis dataKey="full_date" hide={filteredData.length > 72} />
            <YAxis unit=" MW" />
            <Tooltip contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }} />
            <Legend verticalAlign="top" height={50} />

            {activeType === 'solar' && (
              <>
                <Area type="monotone" dataKey="expected_best" stroke="#FFD700" fill="#edcc0eff" fillOpacity={0.4} name="Solar: Best" />
                <Area type="monotone" dataKey="total_hourly_real" stroke="#dd8d2cff" fill="#ef9d39ff" fillOpacity={0.6} name="Solar: Real" />
                <Area type="monotone" dataKey="expected_worst" stroke="#e8390eff" fill="#ed5610ff" fillOpacity={0.8} name="Solar: Worst" />
              </>
            )}

            {activeType === 'wind' && (
              <>
                <Area type="monotone" dataKey="expected_best" stroke="#3498db" fill="#3498db" fillOpacity={0.4} name="Wind: Best" />
                <Area type="monotone" dataKey="total_hourly_real" stroke="#2980b9" fill="#2980b9" fillOpacity={0.6} name="Wind: Real" />
                <Area type="monotone" dataKey="expected_worst" stroke="#1c5980" fill="#1c5980" fillOpacity={0.8} name="Wind: Worst" />
              </>
            )}

            {activeType === 'genel' && (
              <>
                <Area type="monotone" dataKey="solar_real" stroke="#FFD700" fill="#FFD700" fillOpacity={0.3} strokeWidth={3} name="Solar Real" />
                <Area type="monotone" dataKey="wind_real" stroke="#3498db" fill="#3498db" fillOpacity={0.3} strokeWidth={3} name="Wind Real" />
              </>
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default App;