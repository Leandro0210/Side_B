# Cómo reproducir la ablación en Windows PowerShell

1. Copia `auditar_side_b_v0.py` a la carpeta raíz de `side_b_dataset_starter`, **junto a** `side_b_model_v0.py`. No reemplaces el modelo ni el dataset.
2. Desde la raíz del proyecto, ejecuta:

```powershell
.\.venv\Scripts\python.exe auditar_side_b_v0.py --input data\dataset_v1\side_b_dataset.csv --reference data\model_v0\recommendations.csv --out data\auditoria_v0_1 --top-k 10
```

3. Se crearán: `ablation_by_profile.csv`, `ablation_recommendations.csv`, `ablation_overall.csv` y `ablation_manifest.json`.
4. El manifiesto verifica si las variantes A y D coinciden con los resultados del modelo v0 original. En los archivos revisados se comprobó **0 divergencias en 120 posiciones**.

No requiere Internet ni nuevas dependencias si ya ejecutas SIDE B Model v0.1 correctamente.

La política C (popularidad 5 %, sin límite) es una **comparación adicional**, no una recomendación final de despliegue.
