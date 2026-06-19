from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.db.models.addresses import Address
from app.schemas.pagination import PaginatedResponse
from app.schemas.addresses import AddressCreate, AddressUpdate
from app.services.pagination import paginate_scalars


def list_user_addresses(
    db: Session,
    user_id: int,
    *,
    page: int,
    page_size: int,
) -> PaginatedResponse:
    statement = select(Address).where(Address.user_id == user_id).order_by(
        Address.is_default.desc(),
        Address.id,
    )
    return paginate_scalars(db, statement, page=page, page_size=page_size)


def get_user_address(db: Session, *, user_id: int, address_id: int) -> Address | None:
    statement = select(Address).where(
        Address.id == address_id,
        Address.user_id == user_id,
    )
    return db.scalar(statement)


def create_address(db: Session, *, user_id: int, payload: AddressCreate) -> Address:
    is_first_address = not db.scalar(
        select(Address.id).where(Address.user_id == user_id).limit(1)
    )
    address = Address(
        user_id=user_id,
        **payload.model_dump(exclude={"is_default"}),
        is_default=payload.is_default or is_first_address,
    )
    db.add(address)
    if address.is_default:
        _clear_other_defaults(db, user_id=user_id, keep_address=address)
    db.commit()
    db.refresh(address)
    return address


def update_address(
    db: Session,
    *,
    address: Address,
    payload: AddressUpdate,
) -> Address:
    updates = payload.model_dump(exclude_unset=True)
    is_default = updates.pop("is_default", None)

    for field, value in updates.items():
        setattr(address, field, value)

    if is_default is not None:
        address.is_default = is_default
        if is_default:
            _clear_other_defaults(db, user_id=address.user_id, keep_address=address)

    db.commit()
    db.refresh(address)
    return address


def delete_address(db: Session, *, address: Address) -> None:
    db.delete(address)
    db.commit()


def _clear_other_defaults(
    db: Session,
    *,
    user_id: int,
    keep_address: Address,
) -> None:
    statement = (
        update(Address)
        .where(Address.user_id == user_id)
        .where(Address.id != keep_address.id)
        .values(is_default=False)
    )
    db.execute(statement)
