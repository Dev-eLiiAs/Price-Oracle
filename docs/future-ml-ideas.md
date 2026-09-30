# Evolución futura del motor de recomendación

El motor actual (`backend/app/services/advisor.py`) es deliberadamente simple: estadística
descriptiva pura (mínimo histórico, media móvil de 30 días, percentil del precio actual sobre
los últimos 90 días) sin entrenamiento ni infraestructura de ML. Es la base natural para
evolucionar hacia algo más sofisticado una vez haya suficiente histórico multi-producto:

- **Detección de estacionalidad**: identificar patrones recurrentes (Black Friday, rebajas de
  enero/verano) comparando el mismo producto o categoría año contra año.
- **Forecasting de precio**: modelos de series temporales simples (regresión lineal,
  `statsmodels`, o Prophet) para predecir si el precio bajará en los próximos N días en vez de
  solo describir el pasado.
- **Clasificación "comprar ahora vs. esperar"**: un modelo supervisado entrenado sobre outcomes
  históricos reales (¿bajó el precio tras la recomendación?) una vez haya suficientes ejemplos
  etiquetados por el propio uso de la app.

Ninguna de estas ideas es necesaria para el MVP — el enfoque basado en reglas es interpretable,
no requiere dataset ni GPU, y es la progresión pedagógica correcta antes de saltar a ML aplicado.
