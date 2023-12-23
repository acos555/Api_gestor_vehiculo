from datetime import date
import fastapi
import uvicorn
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Date, ForeignKey, BigInteger
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from fastapi import Depends
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import relationship
from sqlalchemy.exc import IntegrityError


Base = declarative_base()


class Propietario(Base):
    __tablename__ = 'propietario'
    __table_args__ = {'schema': 'public'}

    identificacion = Column(BigInteger, primary_key=True)
    nombre = Column(String(50), nullable=False)
    apellido = Column(String(50), nullable=False)
    fecha_nacimiento = Column(String(50), nullable=False)
    direccion = Column(String(255), nullable=False)
    telefono = Column(BigInteger, nullable=False)
    email = Column(String(255), nullable=False)


class Vehiculo(Base):
    __tablename__ = 'vehiculos'
    __table_args__ = {'schema': 'public'}

    placa = Column(String(50), primary_key=True)
    marca = Column(String(50), nullable=False)
    vin = Column(String(50), nullable=False)
    linea = Column(String(50), nullable=False)
    cilindrada = Column(String(50), nullable=False)
    color = Column(String(255), nullable=False)
    chasis = Column(String(20), nullable=False)
    modelo = Column(String(50), nullable=False)
    propietario_identificacion = Column(BigInteger, ForeignKey('public.propietario.identificacion'), nullable=False)
    tipo_vehiculo_id = Column(BigInteger, ForeignKey('public.tipo_vehiculo.id'), nullable=False)
    tipo_vehiculo = relationship('TipoVehiculo', back_populates='vehiculos')



class TipoVehiculo(Base):
    __tablename__ = 'tipo_vehiculo'
    __table_args__ = {'schema': 'public'}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tipo_vehiculo = Column(String(50), nullable=False)
    vehiculos = relationship('Vehiculo', back_populates='tipo_vehiculo')

class PydanticBase(BaseModel):
    class Config:
        orm_mode = True


class PropietarioPydantic(PydanticBase):
    identificacion: int
    nombre: str
    apellido: str
    fecha_nacimiento: date
    direccion: str
    telefono: int
    email: str


class VehiculoPydantic(PydanticBase):
    placa: str
    marca: str
    vin: str
    linea: str
    cilindrada: str
    color: str
    chasis: str
    tipo_vehiculo: str
    modelo: str
    propietario_identificacion: int

class VehiculoCreate(BaseModel):
    placa: str
    marca: str
    vin: str
    linea: str
    cilindrada: str
    color: str
    chasis: str
    tipo_vehiculo: int
    modelo: str
    propietario_identificacion: int


class TipoVehiculoCreate(PydanticBase):
    tipo_vehiculo: str

class TipoVehiculoPydantic(TipoVehiculoCreate):
    id: int


def create_tables(engine):
    Base.metadata.create_all(bind=engine)


class API(fastapi.FastAPI):
    def __init__(self):
        super().__init__()
        self.engine = create_engine(
            "postgresql://postgres:postgres@localhost:5431/Gestor_vehiculos",
            connect_args={'options': '-csearch_path=public'}  
        )
        self.Session = sessionmaker(bind=self.engine)


app = API()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    create_tables(app.engine)


# Dependency to get the database session
def get_db():
    db = app.Session()
    try:
        yield db
    finally:
        db.close()


# Métodos CRUD para Propietario
@app.get("/propietarios", response_model=List[PropietarioPydantic])
async def read_propietarios(db: Session = Depends(get_db)):
    propietarios = db.query(Propietario).all()
    return propietarios


@app.post("/propietarios", response_model=PropietarioPydantic)
async def create_propietario(propietario: PropietarioPydantic, db: Session = Depends(get_db)):
    db_propietario = Propietario(**propietario.dict())
    db.add(db_propietario)
    db.commit()
    return propietario


@app.get("/propietarios/{identificacion}", response_model=PropietarioPydantic)
async def read_propietario(identificacion: int, db: Session = Depends(get_db)):
    db_propietario = db.query(Propietario).filter(Propietario.identificacion == identificacion).first()
    if db_propietario:
        return db_propietario
    raise fastapi.HTTPException(status_code=404, detail="Propietario no encontrado")


@app.put("/propietarios/{identificacion}", response_model=PropietarioPydantic)
async def update_propietario(identificacion: int, propietario: PropietarioPydantic, db: Session = Depends(get_db)):
    db_propietario = db.query(Propietario).filter(Propietario.identificacion == identificacion).first()
    if db_propietario:
        for key, value in propietario.dict().items():
            setattr(db_propietario, key, value)
        db.commit()
        return propietario
    raise fastapi.HTTPException(status_code=404, detail="Propietario no encontrado")


@app.delete("/propietarios/{identificacion}", response_model=PropietarioPydantic)
async def delete_propietario(identificacion: int, db: Session = Depends(get_db)):
    db_propietario = db.query(Propietario).filter(Propietario.identificacion == identificacion).first()
    if db_propietario:
        db.delete(db_propietario)
        db.commit()
        return db_propietario
    raise fastapi.HTTPException(status_code=404, detail="Propietario no encontrado")


# Métodos CRUD para Tipo de Vehiculo
@app.get("/tipos_vehiculo", response_model=List[TipoVehiculoPydantic])
async def read_tipos_vehiculo(db: Session = Depends(get_db)):
    tipos_vehiculo = db.query(TipoVehiculo).all()
    return [TipoVehiculoPydantic(**tipo.__dict__) for tipo in tipos_vehiculo]



@app.post("/tipos_vehiculo", response_model=TipoVehiculoPydantic)
async def create_tipo_vehiculo(tipo_vehiculo_item: TipoVehiculoCreate, db: Session = Depends(get_db)):
    db_tipo_vehiculo = TipoVehiculo(**tipo_vehiculo_item.dict())
    db.add(db_tipo_vehiculo)
    db.commit()
    db.refresh(db_tipo_vehiculo)
    
    # Incluye el ID generado en la respuesta
    tipo_vehiculo_item_with_id = TipoVehiculoPydantic(**db_tipo_vehiculo.__dict__)
    return tipo_vehiculo_item_with_id


@app.get("/tipos_vehiculo/{tipo_vehiculo_id}", response_model=TipoVehiculoPydantic)
async def read_tipo_vehiculo(tipo_vehiculo_id: int, db: Session = Depends(get_db)):
    db_tipo_vehiculo = db.query(TipoVehiculo).filter(TipoVehiculo.id == tipo_vehiculo_id).first()
    if db_tipo_vehiculo:
        return TipoVehiculoPydantic(**db_tipo_vehiculo.__dict__)
    raise fastapi.HTTPException(status_code=404, detail="Tipo de vehiculo no encontrado")



@app.put("/tipos_vehiculo/{tipo_vehiculo_id}", response_model=TipoVehiculoPydantic)
async def update_tipo_vehiculo(tipo_vehiculo_id: int, tipo_vehiculo_item: TipoVehiculoPydantic, db: Session = Depends(get_db)):
    print(f"Datos de solicitud: {tipo_vehiculo_item.dict()}")
    db_tipo_vehiculo = db.query(TipoVehiculo).filter(TipoVehiculo.id == tipo_vehiculo_id).first()
    if db_tipo_vehiculo:
        for key, value in tipo_vehiculo_item.dict().items():
            setattr(db_tipo_vehiculo, key, value)
        db.commit()
        return tipo_vehiculo_item
    raise fastapi.HTTPException(status_code=404, detail="Tipo de vehiculo no encontrado")



@app.delete("/tipos_vehiculo/{tipo_vehiculo_id}", response_model=TipoVehiculoPydantic)
async def delete_tipo_vehiculo(tipo_vehiculo_id: int, db: Session = Depends(get_db)):
    db_tipo_vehiculo = db.query(TipoVehiculo).filter(TipoVehiculo.id == tipo_vehiculo_id).first()
    if db_tipo_vehiculo:
        db.delete(db_tipo_vehiculo)
        db.commit()
        return db_tipo_vehiculo
    raise fastapi.HTTPException(status_code=404, detail="Tipo de vehiculo no encontrado")


# Métodos CRUD para Vehiculo
@app.get("/vehiculos", response_model=List[VehiculoPydantic])
async def read_vehiculos(db: Session = Depends(get_db)):
    vehiculos = (
        db.query(Vehiculo)
        .options(joinedload(Vehiculo.tipo_vehiculo))  # Esto realiza una carga anticipada para el tipo de vehículo
        .all()
    )
    
    return [
        VehiculoPydantic(
            placa=vehiculo.placa,
            marca=vehiculo.marca,
            vin=vehiculo.vin,
            linea=vehiculo.linea,
            cilindrada=vehiculo.cilindrada,
            color=vehiculo.color,
            chasis=vehiculo.chasis,
            tipo_vehiculo=vehiculo.tipo_vehiculo.tipo_vehiculo if vehiculo.tipo_vehiculo else None,
            modelo=vehiculo.modelo,
            propietario_identificacion=vehiculo.propietario_identificacion
        )
        for vehiculo in vehiculos
    ]
    

@app.put("/vehiculos/{placa}", response_model=VehiculoPydantic)
async def update_vehiculo(placa: str, vehiculo: VehiculoCreate, db: Session = Depends(get_db)):
    # Verificar si el vehículo existe
    db_vehiculo = db.query(Vehiculo).filter(Vehiculo.placa == placa).first()

    if not db_vehiculo:
        raise fastapi.HTTPException(status_code=404, detail="Vehículo no encontrado")

    # Verificar si el nuevo propietario existe
    if not db.query(Propietario).filter(Propietario.identificacion == vehiculo.propietario_identificacion).first():
        raise fastapi.HTTPException(status_code=400, detail="Propietario no encontrado")

    # Verificar si el nuevo tipo de vehículo existe
    tipo_vehiculo = db.query(TipoVehiculo).get(vehiculo.tipo_vehiculo)
    if not tipo_vehiculo:
        raise fastapi.HTTPException(status_code=400, detail="Tipo de vehículo no encontrado")

    # Actualizar los campos del vehículo
    db_vehiculo.placa = vehiculo.placa
    db_vehiculo.marca = vehiculo.marca
    db_vehiculo.vin = vehiculo.vin
    db_vehiculo.linea = vehiculo.linea
    db_vehiculo.cilindrada = vehiculo.cilindrada
    db_vehiculo.color = vehiculo.color
    db_vehiculo.chasis = vehiculo.chasis
    db_vehiculo.modelo = vehiculo.modelo
    db_vehiculo.propietario_identificacion = vehiculo.propietario_identificacion
    db_vehiculo.tipo_vehiculo = tipo_vehiculo

    db.commit()
    db.refresh(db_vehiculo)

    return VehiculoPydantic(
        placa=db_vehiculo.placa,
        marca=db_vehiculo.marca,
        vin=db_vehiculo.vin,
        linea=db_vehiculo.linea,
        cilindrada=db_vehiculo.cilindrada,
        color=db_vehiculo.color,
        chasis=db_vehiculo.chasis,
        modelo=db_vehiculo.modelo,
        propietario_identificacion=db_vehiculo.propietario_identificacion,
        tipo_vehiculo=tipo_vehiculo.tipo_vehiculo,
    )
    

@app.get("/vehiculos/{placa}", response_model=VehiculoPydantic)
async def read_vehiculo(placa: str, db: Session = Depends(get_db)):
    db_vehiculo = (
        db.query(Vehiculo)
        .options(joinedload(Vehiculo.tipo_vehiculo))
        .filter(Vehiculo.placa == placa)
        .first()
    )
    if db_vehiculo:
        return VehiculoPydantic(
            placa=db_vehiculo.placa,
            marca=db_vehiculo.marca,
            vin=db_vehiculo.vin,
            linea=db_vehiculo.linea,
            cilindrada=db_vehiculo.cilindrada,
            color=db_vehiculo.color,
            chasis=db_vehiculo.chasis,
            tipo_vehiculo=str(db_vehiculo.tipo_vehiculo.id) if db_vehiculo.tipo_vehiculo else None,
            modelo=db_vehiculo.modelo,
            propietario_identificacion=db_vehiculo.propietario_identificacion
        )
    raise fastapi.HTTPException(status_code=404, detail="Vehiculo no encontrado")


@app.post("/vehiculos", response_model=VehiculoPydantic)
async def create_vehiculo(vehiculo: VehiculoCreate, db: Session = Depends(get_db)):
    db_tipo_vehiculo = db.query(TipoVehiculo).filter(TipoVehiculo.id == vehiculo.tipo_vehiculo).first()
    if not db_tipo_vehiculo:
        raise fastapi.HTTPException(status_code=400, detail="Tipo de vehiculo no encontrado")

    db_vehiculo = Vehiculo(
        placa=vehiculo.placa,
        marca=vehiculo.marca,
        vin=vehiculo.vin,
        linea=vehiculo.linea,
        cilindrada=vehiculo.cilindrada,
        color=vehiculo.color,
        chasis=vehiculo.chasis,
        modelo=vehiculo.modelo,
        propietario_identificacion=vehiculo.propietario_identificacion,
        tipo_vehiculo_id=db_tipo_vehiculo.id,
    )
    db.add(db_vehiculo)
    db.commit()
    db.refresh(db_vehiculo)

    return VehiculoPydantic(
        placa=db_vehiculo.placa,
        marca=db_vehiculo.marca,
        vin=db_vehiculo.vin,
        linea=db_vehiculo.linea,
        cilindrada=db_vehiculo.cilindrada,
        color=db_vehiculo.color,
        chasis=db_vehiculo.chasis,
        modelo=db_vehiculo.modelo,
        propietario_identificacion=db_vehiculo.propietario_identificacion,
        tipo_vehiculo=db_tipo_vehiculo.tipo_vehiculo,  # Asegúrate de tener este campo en tu modelo SQLAlchemy
    )


@app.delete("/vehiculos/{placa}", response_model=VehiculoPydantic)
async def delete_vehiculo(placa: str, db: Session = Depends(get_db)):
    db_vehiculo = (
        db.query(Vehiculo)
        .options(joinedload(Vehiculo.tipo_vehiculo))  # Esto realiza una carga anticipada para el tipo de vehículo
        .filter(Vehiculo.placa == placa)
        .first()
    )

    if db_vehiculo:
        db.delete(db_vehiculo)
        db.commit()
        return VehiculoPydantic(
            placa=db_vehiculo.placa,
            marca=db_vehiculo.marca,
            vin=db_vehiculo.vin,
            linea=db_vehiculo.linea,
            cilindrada=db_vehiculo.cilindrada,
            color=db_vehiculo.color,
            chasis=db_vehiculo.chasis,
            tipo_vehiculo=db_vehiculo.tipo_vehiculo.tipo_vehiculo if db_vehiculo.tipo_vehiculo else None,
            modelo=db_vehiculo.modelo,
            propietario_identificacion=db_vehiculo.propietario_identificacion
        )

    raise fastapi.HTTPException(status_code=404, detail="Vehiculo no encontrado")


@app.get("/datos_propietarios_vehiculos", response_model=List[dict])
async def get_datos_propietarios_vehiculos(db: Session = Depends(get_db)):
    # Obtener todos los propietarios
    propietarios = db.query(Propietario).all()

    datos_propietarios_vehiculos = []
    
    for propietario in propietarios:
        # Para cada propietario, obtener su vehículo (si lo tiene)
        db_vehiculo = (
            db.query(Vehiculo)
            .filter(Vehiculo.propietario_identificacion == propietario.identificacion)
            .first()
        )

        # Crear un diccionario con los datos del propietario y su vehículo (si lo tiene)
        datos = {
            "identificacion": propietario.identificacion,
            "nombre": propietario.nombre,
            "apellido": propietario.apellido,
            "placa": db_vehiculo.placa if db_vehiculo else None,
            "marca": db_vehiculo.marca if db_vehiculo else None,
            "color": db_vehiculo.color if db_vehiculo else None,
        }

        datos_propietarios_vehiculos.append(datos)

    return datos_propietarios_vehiculos

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000, log_level="info")
