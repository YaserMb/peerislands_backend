from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.models.addresses import Address
from app.db.models.users import User
from app.db.session import get_db
from app.schemas.addresses import AddressCreate, AddressRead, AddressUpdate
from app.services.addresses import (
    create_address,
    delete_address,
    get_user_address,
    list_user_addresses,
    update_address,
)


router = APIRouter(prefix="/addresses", tags=["addresses"])


@router.post("", response_model=AddressRead, status_code=status.HTTP_201_CREATED)
def create_saved_address(
    payload: AddressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Address:
    return create_address(db, user_id=current_user.id, payload=payload)


@router.get("", response_model=list[AddressRead])
def list_saved_addresses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Address]:
    return list_user_addresses(db, current_user.id)


@router.get("/{address_id}", response_model=AddressRead)
def read_saved_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Address:
    return _get_owned_address(db, user_id=current_user.id, address_id=address_id)


@router.patch("/{address_id}", response_model=AddressRead)
def update_saved_address(
    address_id: int,
    payload: AddressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Address:
    address = _get_owned_address(db, user_id=current_user.id, address_id=address_id)
    return update_address(db, address=address, payload=payload)


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    address = _get_owned_address(db, user_id=current_user.id, address_id=address_id)
    delete_address(db, address=address)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _get_owned_address(db: Session, *, user_id: int, address_id: int) -> Address:
    address = get_user_address(db, user_id=user_id, address_id=address_id)
    if address is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found",
        )
    return address
