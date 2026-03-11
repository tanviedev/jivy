import React, { useState, useEffect } from "react";
import MapView from "./MapView";

const LOCATION_MAP = {
  "Pune - Shivajinagar": [18.5308, 73.8475],
  "Pune - Kothrud": [18.5074, 73.8077],
  "Pune - Hadapsar": [18.5089, 73.926],
  "Pune - Pimpri": [18.6298, 73.7997],
  "Pune - Viman Nagar": [18.5679, 73.9143]
};

const SYMPTOMS = [
  "Chest Pain",
  "Breathing Difficulty",
  "Fever",
  "Fracture",
  "Headache"
];

const INSURANCE = [
  "No Insurance",
  "Star Health",
  "ICICI Lombard",
  "HDFC Ergo",
  "Care Health"
];

export default function App() {

  const [lat, setLat] = useState(18.5204);
  const [lon, setLon] = useState(73.8567);

  const [useGPS, setUseGPS] = useState(true);
  const [locationName, setLocationName] = useState("Pune - Shivajinagar");

  const [age, setAge] = useState(30);
  const [symptoms, setSymptoms] = useState<string[]>([]);
  const [policy, setPolicy] = useState("No Insurance");

  const [risk, setRisk] = useState("");
  const [hospitals, setHospitals] = useState<any[]>([]);
  const [selectedHospital, setSelectedHospital] = useState<any>(null);

  const [insuranceResult, setInsuranceResult] = useState<any>(null);

  // ================= GPS =================

  useEffect(() => {
    if (!useGPS) return;

    navigator.geolocation.getCurrentPosition(
      pos => {
        setLat(pos.coords.latitude);
        setLon(pos.coords.longitude);
      },
      () => console.log("GPS unavailable")
    );
  }, [useGPS]);

  // ================= FALLBACK =================

  useEffect(() => {
    if (!useGPS) {
      const coords = LOCATION_MAP[locationName];
      setLat(coords[0]);
      setLon(coords[1]);
    }
  }, [locationName, useGPS]);

  // ================= SYMPTOMS =================

  const toggleSymptom = (s: string) => {
    if (symptoms.includes(s))
      setSymptoms(symptoms.filter(x => x !== s));
    else
      setSymptoms([...symptoms, s]);
  };

  // ================= API =================

  const getRecommendation = async () => {

    const res = await fetch("/api/recommend", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        age,
        symptoms,
        lat,
        lon,
        policy
      })
    });

    const data = await res.json();

    setRisk(data.risk);
    setHospitals(data.hospitals);
  };

  // ================= SELECT HOSPITAL =================

  const selectHospital = async (hospital: any) => {

    setSelectedHospital(hospital);

    const res = await fetch("/api/insurance", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        policy,
        hospital_name: hospital.name,
        estimated_cost: hospital.estimated_cost,
        requires_icu:
          symptoms.includes("Chest Pain") ||
          symptoms.includes("Breathing Difficulty")
      })
    });

    const result = await res.json();

    setInsuranceResult(result);
  };

  return (
    <div className="app">

      <h1>🚑 JIVY – Urban Emergency Care Navigator</h1>

      {/* LOCATION */}

      <h2>📍 Location</h2>

      <label>
        <input
          type="checkbox"
          checked={useGPS}
          onChange={() => setUseGPS(!useGPS)}
        />
        Use GPS
      </label>

      {!useGPS && (
        <select
          value={locationName}
          onChange={e => setLocationName(e.target.value)}
        >
          {Object.keys(LOCATION_MAP).map(x => (
            <option key={x}>{x}</option>
          ))}
        </select>
      )}

      {/* PATIENT */}

      <h2>👤 Patient Details</h2>

      <input
        type="number"
        value={age}
        onChange={e => setAge(Number(e.target.value))}
      />

      <h3>Symptoms</h3>

      {SYMPTOMS.map(s => (
        <button
          key={s}
          onClick={() => toggleSymptom(s)}
          className={symptoms.includes(s) ? "selected" : ""}
        >
          {s}
        </button>
      ))}

      <h3>Insurance</h3>

      <select
        value={policy}
        onChange={e => setPolicy(e.target.value)}
      >
        {INSURANCE.map(x => (
          <option key={x}>{x}</option>
        ))}
      </select>

      {/* RECOMMEND */}

      <button onClick={getRecommendation}>
        Get Recommendation
      </button>

      {/* RISK */}

      {risk && (
        <div>
          <h2>⚠️ Risk Level</h2>
          <p>{risk}</p>
        </div>
      )}

      {/* HOSPITALS */}

      {hospitals.map((h, i) => (

        <div key={i} className="hospitalCard">

          <h3>{h.name}</h3>

          <p>Distance: {h.road_km} km</p>

          <p>ETA: {h.eta_min} min</p>

          <p>Cost: ₹{h.estimated_cost}</p>

          <p>Insurance: {h.insurance_status}</p>

          <button
            onClick={() => selectHospital(h)}
          >
            Navigate
          </button>

        </div>

      ))}

      {/* MAP */}

      <MapView
        user={{ lat, lon }}
        hospitals={hospitals}
        selected={selectedHospital}
      />

      {/* INSURANCE */}

      {insuranceResult && (

        <div>

          <h2>Insurance Result</h2>

          <p>Status: {insuranceResult.status}</p>

          <p>{insuranceResult.reason}</p>

        </div>

      )}

    </div>
  );
}