"""Define database models."""
import enum

import sqlalchemy.ext.declarative
import sqlalchemy

# These "from ..." imports are necessary for readability even though
# they are against the general coding guidelines.
from sqlalchemy import (
    Column, Integer, String, ForeignKey, BigInteger, Index, Float)
from sqlalchemy.orm import relationship

Base = sqlalchemy.ext.declarative.declarative_base()


class Machine(Base):  # type: ignore
    """Represent a machine on the shop floor."""

    __tablename__ = 'machine'

    id = Column(Integer, primary_key=True)
    name = Column(String(256), unique=True, nullable=False, index=True)

    works = relationship('MachineState', backref='machine', lazy=True)


class MachineCondition(enum.Enum):
    """Represent machine condition."""

    OFF = "off"
    IDLE = "idle"
    WORKING = "working"
    RETOOLING = "retooling"
    BROKEN = "broken"


class MachineState(Base):  # type: ignore
    """Represent a single work of a machine."""

    # pylint: disable=too-many-instance-attributes

    __tablename__ = 'machine_state'

    id = Column(Integer, primary_key=True)
    machine_id = Column(Integer, ForeignKey('machine.id'), nullable=False)
    start = Column(BigInteger, nullable=False, index=True)
    stop = Column(BigInteger, nullable=False, index=True)
    condition = Column(
        sqlalchemy.Enum(*[cond.value for cond in MachineCondition]),
        nullable=False)
    min_power_consumption = Column(Float, nullable=True)
    max_power_consumption = Column(Float, nullable=True)
    avg_power_consumption = Column(Float, nullable=True)
    total_energy = Column(Float, nullable=True)
    pieces = Column(Integer, nullable=True)


Index('machine_state_start', MachineState.machine_id, MachineState.start)
Index('machine_state_stop', MachineState.machine_id, MachineState.stop)
