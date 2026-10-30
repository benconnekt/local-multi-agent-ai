"""Additional read-only endpoints; register this router under /api/v1."""
from pathlib import Path
from fastapi import APIRouter, HTTPException
from app.trading.data.catalogue import discover

router = APIRouter(prefix='/trading', tags=['trading'])
DATA_DIRECTORY = Path(__file__).resolve().parents[3] / 'data' / 'forex' / 'historical_real'

@router.get('/datasets')
def list_datasets():
    return {'datasets': [{k: v for k, v in item.items() if k != 'candles'} for item in discover(DATA_DIRECTORY)]}

@router.get('/datasets/{dataset_id}/candles')
def dataset_candles(dataset_id: str):
    if not dataset_id.isascii() or len(dataset_id) > 100:
        raise HTTPException(404, 'Dataset not found')
    item = next((entry for entry in discover(DATA_DIRECTORY) if entry['id'] == dataset_id), None)
    if item is None:
        raise HTTPException(404, 'Verified dataset not found')
    return {**{k: v for k, v in item.items() if k != 'candles'},
            'candles': [c.model_dump(mode='json') for c in item['candles']]}
