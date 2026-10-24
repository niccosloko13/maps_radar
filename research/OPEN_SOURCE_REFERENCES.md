# Relas — Open-source references reviewed (2026-10-23)

These projects were reviewed as architectural/UI references. No proprietary Waze/Google assets or code are bundled.

- MapLibre React Native — open-source native vector maps for Android/iOS. MIT-style open ecosystem; use own/proper tiles in production.
  https://github.com/maplibre/maplibre-react-native
- MapLibre Navigation Android — open-source turn-by-turn navigation logic, no telemetry.
  https://github.com/maplibre/maplibre-navigation-android
- route-navigation-engine — dependency-free TypeScript navigation core: route matching, maneuvers, heading/sensor fusion, camera policy; MIT.
  https://github.com/rozenkoyaroslav/route-navigation-engine
- expo-maps-navigation — route banner, progress, voice guidance, simulation, off-route + reroute, alternate routes.
  https://github.com/pgiki/expo-maps-navigation
- GraphHopper Maps — open-source route planner UI patterns.
  https://github.com/graphhopper/graphhopper-maps
- TailAdmin — open-source React/Tailwind admin dashboard patterns; used only as visual/IA reference here, not bundled as a dependency.
  https://github.com/TailAdmin/free-react-tailwind-admin-dashboard

## Direction chosen for Relas

1. Keep current local Python/MapLibre prototype lightweight.
2. Make Admin discovery-first: scans do not auto-publish.
3. Put all publication decisions into a single “Alimentar base” queue.
4. Add live operation logs and persistent source/gap history.
5. Rebrand public driver UI to Relas with a distinct visual system.
6. Native milestone: migrate the driver experience to React Native + MapLibre Native; reuse/test navigation-core concepts rather than rebuilding map matching and camera policy blindly.
