# China Colour Regions interactive map

An audio-free, browser-based map of provincial-level recording locations in the Colour Regions collection. Province borders come from Tianditu national-standard vector geometry, distributed in GeoJSON format by [GeoJSON.cn](https://geojson.cn/data/atlas/tiandi). The map uses [MapLibre GL JS](https://maplibre.org/maplibre-gl-js/docs/) to render and interact with the provincial polygons.

## Run locally

From the repository root, regenerate the summary bundle and serve the folder over HTTP:

```powershell
& 'C:\Users\ruilu\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' web/china-map/build_data.py
cd web/china-map
python -m http.server 8000
```

Open `http://localhost:8000`. The page loads MapLibre GL JS and its fonts from public CDNs. The boundary GeoJSON is included locally, so no basemap tile service is required.

## Data policy

- The fill counts recordings whose `metadata/recordings.csv` province exactly maps to a province-level geometry.
- Cross-province, non-standard, blank, and otherwise ambiguous province labels are not allocated to a polygon. The page reports the number excluded from the province layer.
- The collection's cultural-region classification is separate; the selected province profile shows a count breakdown by cultural region.
- The page links out to the recording's source URL. It does not download, embed, or redistribute audio.
- Boundary line features are excluded; the 34 provincial-level administrative units are rendered.

The source geometry is derived from public Tianditu/GeoJSON.cn vectors and simplified for web display. For research requiring legally authoritative boundaries or survey-grade precision, cite and obtain the relevant official dataset directly from the National Geomatics Center of China. See [China's public map-data portal](https://www.webmap.cn/main.do?method=index1).
