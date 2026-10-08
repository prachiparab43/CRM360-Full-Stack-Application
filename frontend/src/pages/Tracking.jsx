import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import api from '../api';
import { MapPin, LogIn, LogOut, CheckCircle } from 'lucide-react';

// Fix leaflet icon issue in react
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

function MapUpdater({ center }) {
  const map = import('react-leaflet').then(m => m.useMap ? m.useMap() : null);
  // Leaflet hooks need to be used properly. The easiest way without an extra hook is:
  // But wait, useMap requires react-leaflet to be imported as a component. Let's just do a simpler key remount.
}

export default function Tracking() {
  const [locations, setLocations] = useState([]);
  const [visits, setVisits] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeCheckin, setActiveCheckin] = useState(false);
  const [mapCenter, setMapCenter] = useState([37.7749, -122.4194]);

  const fetchTracking = async () => {
    try {
      const [locRes, visRes] = await Promise.all([
        api.get('/tracking/locations/latest'),
        api.get('/visits/')
      ]);
      setLocations(locRes.data);
      setVisits(visRes.data);
      if (locRes.data && locRes.data.length > 0) {
        setMapCenter([locRes.data[0].latitude, locRes.data[0].longitude]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => { fetchTracking(); }, []);

  const handleCheckIn = () => {
    if ("geolocation" in navigator) {
      setLoading(true);
      navigator.geolocation.getCurrentPosition(async (pos) => {
        try {
          await api.post('/tracking/check-in', {
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude
          });
          setActiveCheckin(true);
          setMapCenter([pos.coords.latitude, pos.coords.longitude]);
          fetchTracking();
        } catch (err) {
          alert('Check-in failed');
        } finally {
          setLoading(false);
        }
      });
    } else {
      alert('Geolocation is not supported by your browser.');
    }
  };

  const handleCheckOut = () => {
    if ("geolocation" in navigator) {
      setLoading(true);
      navigator.geolocation.getCurrentPosition(async (pos) => {
        try {
          await api.post('/tracking/check-out', {
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude
          });
          setActiveCheckin(false);
          setMapCenter([pos.coords.latitude, pos.coords.longitude]);
          fetchTracking();
        } catch (err) {
          alert('Check-out failed');
        } finally {
          setLoading(false);
        }
      });
    }
  };

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Geo Tracking & Visits</h1>
        <div className="flex gap-3">
          <button disabled={loading || activeCheckin} onClick={handleCheckIn} className="bg-emerald-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-emerald-700 disabled:opacity-50">
            <LogIn size={18} /> Check In
          </button>
          <button disabled={loading || !activeCheckin} onClick={handleCheckOut} className="bg-red-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-red-700 disabled:opacity-50">
            <LogOut size={18} /> Check Out
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden h-[400px]">
        <MapContainer key={mapCenter.join(',')} center={mapCenter} zoom={13} scrollWheelZoom={false} className="h-full w-full">
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="&copy; OpenStreetMap" />
          {locations.map(loc => (
            <Marker key={loc.id} position={[loc.latitude, loc.longitude]}>
              <Popup>Employee ID: {loc.employee_id} <br/> Time: {loc.timestamp}</Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-bold mb-4">Customer Visits</h2>
        {visits.length === 0 ? <p className="text-gray-500">No visits logged.</p> : (
          <ul className="space-y-4">
            {visits.map(v => (
              <li key={v.id} className="border-b pb-4 flex justify-between items-center">
                <div>
                  <div className="font-semibold">{v.purpose}</div>
                  <div className="text-sm text-gray-500">Status: <span className="font-medium text-blue-600">{v.status}</span></div>
                </div>
                {v.status !== 'Completed' && (
                  <button className="text-green-600 flex items-center gap-1 hover:bg-green-50 px-2 py-1 rounded text-sm"><CheckCircle size={16}/> Complete</button>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}


