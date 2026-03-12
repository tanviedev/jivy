import { MapContainer, TileLayer, Marker, Polyline } from "react-leaflet";
import "leaflet/dist/leaflet.css";

export default function MapView({ user, hospitals, selected }: any) {

  return (
    <div style={{ width: "100%", height: "500px" }}>

      <MapContainer
        center={[user.lat, user.lon]}
        zoom={13}
        style={{ width: "100%", height: "100%" }}
      >

        <TileLayer
          attribution='&copy; OpenStreetMap'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* USER */}
        <Marker position={[user.lat, user.lon]} />

        {/* HOSPITALS */}
        {hospitals.map((h: any, i: number) => (
          <Marker key={i} position={[h.lat, h.long]} />
        ))}

        {/* ROUTE */}
        {selected && (
          <Polyline
            positions={selected.route}
            color="red"
          />
        )}

      </MapContainer>

    </div>
  );
}