import streamlit as st
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, Integer, String, Date, Float, ForeignKey, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship, declarative_base
from db_config import get_engine
from datetime import datetime, timedelta, date
import io

Base = declarative_base()

class Cliente(Base):
    __tablename__ = 'clientes'
    ID = Column(Integer, primary_key=True)  # No autoincremental
    NombreCliente = Column(String)
    PlanMB = Column(String)
    FechaInstalacion = Column(Date)
    TipoServicioID = Column(Integer, ForeignKey('tipo_servicio.ID'))
    Tarifa = Column(Float)
    IPAddress = Column(String)
    Telefono = Column(String)
    Ubicacion = Column(String)
    Cedula = Column(String)
    pagos = relationship('Pago', backref='cliente')

class TipoServicio(Base):
    __tablename__ = 'tipo_servicio'
    ID = Column(Integer, primary_key=True, autoincrement=True)
    Tipo = Column(String)

class Pago(Base):
    __tablename__ = 'pagos'
    ID = Column(Integer, primary_key=True, autoincrement=True)
    ClienteID = Column(Integer, ForeignKey('clientes.ID'))
    FechaPago = Column(Date)
    Mes = Column(String)
    Ano = Column(Integer)
    Monto = Column(Float)

engine = get_engine()
Session = sessionmaker(bind=engine)
session = Session()

st.title('Dashboard de Voz IP Company')

# Obtener datos de clientes
clientes = session.query(Cliente).all()
cliente_data = [
    {
        'ID': cliente.ID,
        'Nombre': cliente.NombreCliente,
        'Plan': cliente.PlanMB,
        'Fecha Instalacion': cliente.FechaInstalacion,
        'Tarifa': cliente.Tarifa,
        'IP Address': cliente.IPAddress,
        'Telefono': cliente.Telefono,
        'Ubicacion': cliente.Ubicacion,
        'Cedula': cliente.Cedula
    } for cliente in clientes
]

df_clientes = pd.DataFrame(cliente_data)

# Función para mostrar y editar datos de clientes
def mostrar_clientes(df, page, rows_per_page):
    start = page * rows_per_page
    end = start + rows_per_page
    df_page = df.iloc[start:end]
    st.write(df_page.to_html(escape=False), unsafe_allow_html=True)
    total_pages = (len(df) + rows_per_page - 1) // rows_per_page
    return total_pages

def agregar_cliente():
    st.subheader('Agregar nuevo Cliente')
    nombre_cliente = st.text_input('Nombre del Cliente', key='nuevo_nombre')
    plan_mb = st.text_input('Plan MB', key='nuevo_plan')
    fecha_instalacion = st.date_input('Fecha de Instalación', key='nuevo_fecha')
    tarifa = st.number_input('Tarifa', key='nuevo_tarifa', min_value=0.0)
    ip_address = st.text_input('IP Address', key='nuevo_ip')
    telefono = st.text_input('Telefono', key='nuevo_telefono')
    ubicacion = st.text_input('Ubicacion', key='nuevo_ubicacion')
    cedula = st.text_input('Cedula', key='nuevo_cedula')
    tipo_servicio = st.selectbox('Tipo de Servicio', [('Fibra Optica', 1), ('WLAN', 2)], format_func=lambda x: x[0], key='nuevo_tipo_servicio')

    if st.button('Agregar Cliente'):
        id = session.query(Cliente).count() + 1
        while True:
            try:
                nuevo_cliente = Cliente(
                    ID=id,
                    NombreCliente=nombre_cliente,
                    PlanMB=plan_mb,
                    FechaInstalacion=fecha_instalacion,
                    TipoServicioID=tipo_servicio[1],
                    Tarifa=tarifa,
                    IPAddress=ip_address,
                    Telefono=telefono,
                    Ubicacion=ubicacion,
                    Cedula=cedula
                )
                session.add(nuevo_cliente)
                session.commit()
                st.success('Cliente agregado exitosamente')
                st.experimental_rerun()
                break
            except IntegrityError:
                session.rollback()
                id += 1

def editar_cliente():
    st.subheader('Editar Cliente')
    cliente_id = st.number_input('ID del Cliente', key='edit_id', min_value=1)
    cliente = session.query(Cliente).filter_by(ID=cliente_id).first()
    if cliente:
        nombre_cliente = st.text_input('Nombre del Cliente', cliente.NombreCliente, key='edit_nombre')
        plan_mb = st.text_input('Plan MB', cliente.PlanMB, key='edit_plan')
        fecha_instalacion = st.date_input('Fecha de Instalación', cliente.FechaInstalacion, key='edit_fecha')
        tarifa = st.number_input('Tarifa', value=cliente.Tarifa, key='edit_tarifa')
        ip_address = st.text_input('IP Address', cliente.IPAddress, key='edit_ip')
        telefono = st.text_input('Telefono', cliente.Telefono, key='edit_telefono')
        ubicacion = st.text_input('Ubicacion', cliente.Ubicacion, key='edit_ubicacion')
        cedula = st.text_input('Cedula', cliente.Cedula, key='edit_cedula')
        tipo_servicio = st.selectbox('Tipo de Servicio', [('Fibra Optica', 1), ('WLAN', 2)], index=0 if cliente.TipoServicioID == 1 else 1, format_func=lambda x: x[0], key='edit_tipo_servicio')

        if st.button('Guardar Cambios'):
            cliente.NombreCliente = nombre_cliente
            cliente.PlanMB = plan_mb
            cliente.FechaInstalacion = fecha_instalacion
            cliente.TipoServicioID = tipo_servicio[1]
            cliente.Tarifa = tarifa
            cliente.IPAddress = ip_address
            cliente.Telefono = telefono
            cliente.Ubicacion = ubicacion
            cliente.Cedula = cedula
            session.commit()
            st.success('Cliente editado exitosamente')
            st.experimental_rerun()
    else:
        st.warning('Cliente no encontrado')

def eliminar_cliente():
    st.subheader('Eliminar Cliente')
    cliente_id = st.number_input('ID del Cliente a eliminar', key='delete_id', min_value=1)
    if st.button('Eliminar Cliente'):
        session.execute(delete(Cliente).where(Cliente.ID == cliente_id))
        session.commit()
        st.success('Cliente eliminado exitosamente')
        st.experimental_rerun()

def buscar_cliente(df):
    st.subheader('Buscar Cliente')
    buscar_por = st.selectbox('Buscar por', df.columns.tolist(), key='buscar_por')
    buscar_valor = st.text_input(f'Valor para buscar en {buscar_por}', key='buscar_valor')
    if st.button('Buscar'):
        df_busqueda = df[df[buscar_por].astype(str).str.contains(buscar_valor, na=False)]
        if not df_busqueda.empty:
            mostrar_clientes(df_busqueda, 0, len(df_busqueda))
        else:
            st.warning('No se encontraron resultados')

# Mapeo de los meses en español a números
meses_map = {
    "ENERO": 1,
    "FEBRERO": 2,
    "MARZO": 3,
    "ABRIL": 4,
    "MAYO": 5,
    "JUNIO": 6,
    "JULIO": 7,
    "AGOSTO": 8,
    "SEPTIEMBRE": 9,
    "OCTUBRE": 10,
    "NOVIEMBRE": 11,
    "DICIEMBRE": 12
}

# Función para mostrar morosos
def mostrar_morosos():
    st.subheader('Clientes Morosos')
    clientes_morosos = []
    hoy = date.today()
    for cliente in clientes:
        if cliente.Tarifa is None or cliente.Tarifa == 0.0:
            continue

        pagos = session.query(Pago).filter(Pago.ClienteID == cliente.ID, Pago.Ano >= 2024).all()

        # Crear un set con los meses pagados desde enero 2024 hasta el mes actual
        meses_pagados = set((pago.Ano, meses_map[pago.Mes.upper()]) for pago in pagos if pago.Ano >= 2024)
        
        # Crear un set con todos los meses desde la instalación del servicio hasta el mes actual
        meses_totales = set()
        inicio_calculo = max(date(2024, 1, 1), cliente.FechaInstalacion)
        for ano in range(inicio_calculo.year, hoy.year + 1):
            for mes in range(1, 13):
                if (ano == inicio_calculo.year and mes < inicio_calculo.month) or (ano == hoy.year and mes > hoy.month):
                    continue
                meses_totales.add((ano, mes))

        # Calcular los meses de deuda
        meses_deuda = meses_totales - meses_pagados
        if len(meses_deuda) >= 3:
            total_deuda = len(meses_deuda) * cliente.Tarifa
            clientes_morosos.append({
                'ID': cliente.ID,
                'Nombre': cliente.NombreCliente,
                'Telefono': cliente.Telefono,
                'Ubicacion': cliente.Ubicacion,
                'Meses Deuda': len(meses_deuda),
                'Monto Deuda': total_deuda
            })

    if clientes_morosos:
        df_morosos = pd.DataFrame(clientes_morosos)
        st.write(df_morosos.to_html(escape=False), unsafe_allow_html=True)
        
        # Botón para descargar el DataFrame como Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_morosos.to_excel(writer, index=False, sheet_name='Morosos')
        output.seek(0)
        
        st.download_button(
            label="Descargar morosos en Excel",
            data=output,
            file_name='clientes_morosos.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        st.write("No hay clientes morosos de más de 3 meses.")

# Función para agregar pagos
def agregar_pago():
    st.subheader('Agregar Pago')
    buscar_por = st.selectbox('Buscar cliente por', ['Nombre', 'Cedula'], key='buscar_pago_por')
    buscar_valor = st.text_input(f'Valor para buscar {buscar_por}', key='buscar_pago_valor')

    cliente = None
    if st.button('Buscar Cliente'):
        if buscar_por == 'Nombre':
            cliente = session.query(Cliente).filter(Cliente.NombreCliente.contains(buscar_valor)).first()
        else:
            cliente = session.query(Cliente).filter(Cliente.Cedula.contains(buscar_valor)).first()

        if cliente:
            st.session_state.cliente_seleccionado = cliente.ID
            st.success(f'Cliente encontrado: {cliente.NombreCliente}, ID: {cliente.ID}')
        else:
            st.warning('Cliente no encontrado')

    if 'cliente_seleccionado' in st.session_state:
        cliente_id = st.session_state.cliente_seleccionado
        cliente = session.query(Cliente).filter_by(ID=cliente_id).first()
        if cliente:
            st.write(f'Cliente seleccionado: {cliente.NombreCliente}, ID: {cliente.ID}')
            
            # Mostrar pagos realizados
            pagos = session.query(Pago).filter_by(ClienteID=cliente.ID).all()
            if pagos:
                pagos_data = [
                    {'ID': pago.ID, 'Fecha de Pago': pago.FechaPago, 'Mes': pago.Mes, 'Año': pago.Ano, 'Monto': pago.Monto}
                    for pago in pagos
                ]
                df_pagos = pd.DataFrame(pagos_data)
                st.write(df_pagos.to_html(escape=False), unsafe_allow_html=True)
            else:
                st.write('No hay pagos registrados para este cliente.')

            # Formulario para agregar nuevo pago
            fecha_pago = st.date_input('Fecha de Pago', date.today(), key='fecha_pago')
            mes_pago = st.selectbox('Mes de Pago', list(meses_map.keys()), key='mes_pago')
            ano_pago = st.number_input('Año de Pago', min_value=2020, value=date.today().year, key='ano_pago')
            monto_pago = st.number_input('Monto de Pago', min_value=0.0, key='monto_pago')

            if st.button('Agregar Pago'):
                nuevo_pago = Pago(
                    ClienteID=cliente.ID,
                    FechaPago=fecha_pago,
                    Mes=mes_pago,
                    Ano=ano_pago,
                    Monto=monto_pago
                )
                session.add(nuevo_pago)
                session.commit()
                st.success('Pago agregado exitosamente')
                del st.session_state.cliente_seleccionado
                st.experimental_rerun()

# Paginación
rows_per_page = 20
page = st.number_input('Página', min_value=1, max_value=(len(df_clientes) + rows_per_page - 1) // rows_per_page, step=1) - 1
total_pages = mostrar_clientes(df_clientes, page, rows_per_page)

# Mostrar navegación de página
st.write(f'Página {page + 1} de {total_pages}')

buscar_cliente(df_clientes)
agregar_cliente()
editar_cliente()
eliminar_cliente()
mostrar_morosos()
agregar_pago()

session.close()
