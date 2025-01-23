import streamlit as st
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, Integer, String, Date, Float, ForeignKey
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship, declarative_base
from datetime import date, timedelta, datetime
import hashlib
import time
import io  # Para trabajar con la creación del archivo Excel en memoria
from db_config import get_engine
import xlsxwriter  # Para escribir archivos Excel
import pywhatkit as kit  # Para enviar mensajes por WhatsApp
from calendar import monthrange

# Conexión a Redis para usar caché
Base = declarative_base()

# Definir el mapeo de los meses a números
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

# Definir la tabla master_users para el manejo de usuarios
class MasterUser(Base):
    __tablename__ = 'master_users'
    ID = Column(Integer, primary_key=True, autoincrement=True)
    Cedula = Column(String)
    Telefono = Column(String)
    Nombre = Column(String)
    User = Column(String)
    Password = Column(String)
    Funcion = Column(String)

class Cliente(Base):
    __tablename__ = 'clientes'
    ID = Column(Integer, primary_key=True)
    NombreCliente = Column(String)
    PlanMB = Column(String)
    FechaInstalacion = Column(Date)
    TipoServicioID = Column(Integer, ForeignKey('tipo_servicio.ID'))
    Tarifa = Column(Float)
    IPAddress = Column(String)
    Telefono = Column(String)
    Ubicacion = Column(String)
    Cedula = Column(String)
    EstadoID = Column(Integer, ForeignKey('Estados.ID'))
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
    Metodo_de_PagoID = Column(Integer, ForeignKey('Metodo_de_Pago.ID'))

class Estado(Base):
    __tablename__ = 'Estados'
    ID = Column(Integer, primary_key=True)
    Estado = Column(String)

class MetodoDePago(Base):
    __tablename__ = 'Metodo_de_Pago'
    ID = Column(Integer, primary_key=True)
    Metodo = Column(String)

engine = get_engine()
Session = sessionmaker(bind=engine)
session = Session()

# Función para hashear la contraseña
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Función para verificar la contraseña
def verificar_password(stored_password, provided_password):
    return stored_password == hash_password(provided_password)

# Función de inicio de sesión
def login():
    st.title("Iniciar Sesión")
    
    username = st.text_input("Nombre de Usuario")
    password = st.text_input("Contraseña", type="password")
    
    if st.button("Iniciar Sesión"):
        if username and password:
            # Buscar el usuario en la base de datos
            usuario = session.query(MasterUser).filter_by(User=username).first()
            if usuario and verificar_password(usuario.Password, password):
                st.success(f"Bienvenido {usuario.Nombre}")
                st.session_state.logged_in = True
                st.session_state.usuario = usuario
                st.experimental_rerun()  # Recargar la página después de iniciar sesión
            else:
                st.error("Nombre de usuario o contraseña incorrectos.")
        else:
            st.error("Por favor, ingresa el nombre de usuario y la contraseña.")

# Formulario para crear un nuevo usuario
def crear_usuario():
    st.subheader("Crear Nuevo Usuario")

    nombre = st.text_input("Nombre Completo")
    cedula = st.text_input("Cédula")
    telefono = st.text_input("Teléfono")
    funcion = st.text_input("Función")
    username = st.text_input("Nombre de Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Crear Usuario"):
        if nombre and cedula and telefono and funcion and username and password:
            # Hashear la contraseña
            password_hash = hash_password(password)

            # Crear el nuevo usuario en la base de datos
            nuevo_usuario = MasterUser(
                Cedula=cedula,
                Telefono=telefono,
                Nombre=nombre,
                User=username,
                Password=password_hash,
                Funcion=funcion
            )
            try:
                session.add(nuevo_usuario)
                session.commit()
                st.success(f"Usuario '{username}' creado exitosamente.")
            except IntegrityError:
                session.rollback()
                st.error("Error al crear el usuario. Es posible que el nombre de usuario ya exista.")
        else:
            st.error("Por favor, completa todos los campos.")

# Función para obtener estadísticas de clientes y pagos
def obtener_estadisticas(anio_seleccionado=None):
    # Contar clientes por estado (sin filtro de año)
    total_clientes = session.query(Cliente).count()
    clientes_activos = session.query(Cliente).filter(Cliente.EstadoID == 1).count()  # EstadoID=1 es 'activo'
    clientes_retirados = session.query(Cliente).filter(Cliente.EstadoID == 2).count()  # EstadoID=2 es 'retirado'
    clientes_suspendidos = session.query(Cliente).filter(Cliente.EstadoID == 3).count()  # EstadoID=3 es 'suspendido'

    # Calcular ingresos mensuales (filtro de año si se selecciona)
    ingresos_por_mes = {}
    if anio_seleccionado:
        for mes_num in range(1, 13):
            pagos_mes = session.query(Pago).filter(
                Pago.Ano == anio_seleccionado,
                Pago.Mes == list(meses_map.keys())[mes_num - 1]  # Usamos el mapeo de meses a texto
            ).all()
            
            total_mes = sum([pago.Monto for pago in pagos_mes])
            ingresos_por_mes[list(meses_map.keys())[mes_num - 1].capitalize()] = total_mes
    else:
        # Si no se selecciona un año, inicializamos ingresos en 0
        ingresos_por_mes = {list(meses_map.keys())[mes_num - 1].capitalize(): 0 for mes_num in range(1, 13)}

    return {
        'total_clientes': total_clientes,
        'clientes_activos': clientes_activos,
        'clientes_retirados': clientes_retirados,
        'clientes_suspendidos': clientes_suspendidos,
        'ingresos_por_mes': ingresos_por_mes
    }

# Función para exportar los clientes a Excel con Ubicación
def exportar_clientes_excel():
    # Obtener todos los clientes con sus datos relevantes
    clientes = session.query(Cliente).all()
    cliente_data = [
        {
            'Nombre': cliente.NombreCliente,
            'Cédula': cliente.Cedula,
            'Fecha de Instalación': cliente.FechaInstalacion,
            'Tarifa': cliente.Tarifa,
            'Ubicación': cliente.Ubicacion,
            'Estado': session.query(Estado).filter_by(ID=cliente.EstadoID).first().Estado
        } for cliente in clientes
    ]

    df_clientes = pd.DataFrame(cliente_data)

    # Crear un archivo Excel en memoria
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_clientes.to_excel(writer, index=False, sheet_name='Clientes')

    output.seek(0)  # Reposicionar el cursor al principio del archivo en memoria
    return output

# Función para mostrar las estadísticas en el Dashboard y generar el Excel
def dashboard():
    st.title('Dashboard de Voz IP Company')

    # Selección del año para ingresos mensuales
    hoy = date.today()
    anio_seleccionado = st.selectbox(
        "Seleccione el año para filtrar ingresos",
        range(2024, hoy.year + 1),  # Años desde 2024 hasta el año actual
        index=(hoy.year - 2024)
    )

    # Obtener estadísticas con el año seleccionado
    stats = obtener_estadisticas(anio_seleccionado)

    # Mostrar el total de clientes y su distribución (sin depender del año)
    st.header("Estadísticas Generales de Clientes")
    st.write(f"Total de Clientes: {stats['total_clientes']}")
    st.write(f"Clientes Activos: {stats['clientes_activos']}")
    st.write(f"Clientes Retirados: {stats['clientes_retirados']}")
    st.write(f"Clientes Suspendidos: {stats['clientes_suspendidos']}")
    
    # Mostrar ingresos mensuales filtrados por el año
    st.header(f"Ingresos Mensuales ({anio_seleccionado})")
    ingresos_df = pd.DataFrame(list(stats['ingresos_por_mes'].items()), columns=['Mes', 'Ingresos'])
    st.bar_chart(ingresos_df.set_index('Mes'))
    st.table(ingresos_df)

    # Exportar clientes a Excel
    st.header("Exportar Clientes a Excel")
    output = exportar_clientes_excel()
    st.download_button(
        label="Descargar Excel de Clientes",
        data=output,
        file_name='clientes.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# Función para mostrar los clientes en la tabla (paginación)
def mostrar_clientes(df, page, rows_per_page):
    start = page * rows_per_page
    end = start + rows_per_page
    df_page = df.iloc[start:end]
    st.write(df_page.to_html(escape=False), unsafe_allow_html=True)
    total_pages = (len(df) + rows_per_page - 1) // rows_per_page
    return total_pages

def agregar_cliente():
    st.subheader('Agregar nuevo Cliente')
    nombre_cliente = st.text_input('Nombre del Cliente', key='nuevo_nombre').lower()
    plan_mb = st.text_input('Plan MB', key='nuevo_plan').lower()
    fecha_instalacion = st.date_input('Fecha de Instalación', key='nuevo_fecha')
    estado = st.selectbox('Estado', session.query(Estado).all(), format_func=lambda x: x.Estado, key='nuevo_estado')
    tarifa = st.number_input('Tarifa', key='nuevo_tarifa', min_value=0.0, disabled=(estado.Estado in ['retirado', 'suspendido']))
    ip_address = st.text_input('IP Address', key='nuevo_ip').lower()
    telefono = st.text_input('Telefono', key='nuevo_telefono').lower()
    ubicacion = st.text_input('Ubicacion', key='nuevo_ubicacion').lower()
    cedula = st.text_input('Cedula', key='nuevo_cedula').lower()
    tipo_servicio = st.selectbox('Tipo de Servicio', session.query(TipoServicio).all(), format_func=lambda x: x.Tipo, key='nuevo_tipo_servicio')

    if st.button('Agregar Cliente'):
        id = session.query(Cliente).count() + 1
        while True:
            try:
                if estado.Estado in ['retirado', 'suspendido']:
                    tarifa = 0.0  # Asigna tarifa a 0 si el estado es retirado o suspendido
                nuevo_cliente = Cliente(
                    ID=id,
                    NombreCliente=nombre_cliente,
                    PlanMB=plan_mb,
                    FechaInstalacion=fecha_instalacion,
                    TipoServicioID=tipo_servicio.ID,
                    Tarifa=tarifa,
                    IPAddress=ip_address,
                    Telefono=telefono,
                    Ubicacion=ubicacion,
                    Cedula=cedula,
                    EstadoID=estado.ID
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
        nombre_cliente = st.text_input('Nombre del Cliente', cliente.NombreCliente or '', key='edit_nombre')
        nombre_cliente = nombre_cliente.lower() if nombre_cliente else ''
        
        plan_mb = st.text_input('Plan MB', cliente.PlanMB or '', key='edit_plan')
        plan_mb = plan_mb.lower() if plan_mb else ''
        
        fecha_instalacion = st.date_input('Fecha de Instalación', cliente.FechaInstalacion, key='edit_fecha')
        
        estado = st.selectbox('Estado', session.query(Estado).all(), index=cliente.EstadoID - 1, format_func=lambda x: x.Estado, key='edit_estado')
        
        tarifa = st.number_input('Tarifa', value=cliente.Tarifa or 0.0, key='edit_tarifa', min_value=0.0, disabled=(estado.Estado in ['retirado', 'suspendido']))
        
        ip_address = st.text_input('IP Address', cliente.IPAddress or '', key='edit_ip')
        ip_address = ip_address.lower() if ip_address else ''
        
        telefono = st.text_input('Telefono', cliente.Telefono or '', key='edit_telefono')
        telefono = telefono.lower() if telefono else ''
        
        ubicacion = st.text_input('Ubicacion', cliente.Ubicacion or '', key='edit_ubicacion')
        ubicacion = ubicacion.lower() if ubicacion else ''
        
        cedula = st.text_input('Cedula', cliente.Cedula or '', key='edit_cedula')
        cedula = cedula.lower() if cedula else ''
        
        tipo_servicio = st.selectbox('Tipo de Servicio', session.query(TipoServicio).all(), index=cliente.TipoServicioID - 1, format_func=lambda x: x.Tipo, key='edit_tipo_servicio')

        if st.button('Guardar Cambios'):
            cliente.NombreCliente = nombre_cliente
            cliente.PlanMB = plan_mb
            cliente.FechaInstalacion = fecha_instalacion
            cliente.TipoServicioID = tipo_servicio.ID
            cliente.EstadoID = estado.ID
            if estado.Estado in ['retirado', 'suspendido']:
                cliente.Tarifa = 0.0  # Establece la tarifa a 0 si el estado es retirado o suspendido
            else:
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

def buscar_cliente(df):
    st.subheader('Buscar Cliente')
    
    # Agregamos "Tipo de Servicio" a las opciones de búsqueda
    opciones_busqueda = df.columns.tolist() + ['Tipo de Servicio']
    buscar_por = st.selectbox('Buscar por', opciones_busqueda, key='buscar_por')
    
    buscar_valor = st.text_input(f'Valor para buscar en {buscar_por}', key='buscar_valor').lower()
    
    if st.button('Buscar'):
        if buscar_por == 'Tipo de Servicio':
            tipo_servicio = session.query(TipoServicio).filter(TipoServicio.Tipo.ilike(f"%{buscar_valor}%")).first()
            if tipo_servicio:
                df_busqueda = df[df['Tipo de Servicio'].str.lower() == tipo_servicio.Tipo.lower()]
            else:
                df_busqueda = pd.DataFrame()  # No se encontró el tipo de servicio
        else:
            df_busqueda = df[df[buscar_por].astype(str).str.lower().str.contains(buscar_valor, na=False)]
        
        if not df_busqueda.empty:
            mostrar_clientes(df_busqueda, 0, len(df_busqueda))
        else:
            st.warning('No se encontraron resultados')

def mostrar_morosos():
    st.subheader('Clientes Morosos')

    # Selección del número mínimo de meses de deuda
    meses_deuda_minima = st.selectbox(
        'Mostrar clientes con deuda de:',
        ['1 mes o más', '2 meses o más', '3 meses o más', '4 meses o más', '5 meses o más'],
        index=2  # Por defecto, seleccionamos '3 meses o más'
    )

    # Convertimos la selección a un número entero
    meses_deuda_minima = int(meses_deuda_minima.split()[0])

    clientes_morosos = []
    hoy = date.today()

    for cliente in clientes:
        # Omitimos clientes con tarifa nula
        if cliente.Tarifa is None or cliente.Tarifa == 0.0:
            continue

        # Verificamos el estado del cliente
        if cliente.EstadoID in [2, 3]:  # Suspendido o retirado
            continue

        # Fecha de corte personalizada basada en la instalación
        dia_corte = cliente.FechaInstalacion.day

        # Tomar el último pago registrado del cliente
        pagos = session.query(Pago).filter(Pago.ClienteID == cliente.ID).order_by(Pago.Ano.desc(), Pago.Mes.desc()).all()
        if pagos:
            # Validar el mes del último pago
            ultimo_pago = pagos[0]
            mes_upper = ultimo_pago.Mes.upper().strip()  # Normalizamos el mes
            if mes_upper not in meses_map:
                st.warning(f"El mes '{ultimo_pago.Mes}' del cliente {cliente.NombreCliente} no es válido. Ignorando cliente.")
                continue

            # Validar el día de corte ajustándolo al último día del mes si es necesario
            ano = ultimo_pago.Ano
            mes = meses_map[mes_upper]
            ultimo_dia_del_mes = monthrange(ano, mes)[1]  # Obtiene el último día del mes
            dia_ajustado = min(dia_corte, ultimo_dia_del_mes)  # Ajusta el día si excede el máximo permitido

            try:
                fecha_ultimo_pago = date(ano, mes, dia_ajustado)
            except Exception as e:
                st.error(f"Error al calcular la fecha del último pago para el cliente {cliente.NombreCliente}: {e}")
                continue
        else:
            # Si no hay pagos, usamos la fecha de instalación o el inicio de 2024
            fecha_instalacion_ajustada = min(
                cliente.FechaInstalacion.day,
                monthrange(cliente.FechaInstalacion.year, cliente.FechaInstalacion.month)[1]
            )
            fecha_ultimo_pago = max(date(2024, 1, 1), cliente.FechaInstalacion.replace(day=fecha_instalacion_ajustada))

        # Crear un conjunto de los meses desde el último pago hasta hoy
        meses_totales = set()
        for ano in range(fecha_ultimo_pago.year, hoy.year + 1):
            for mes in range(1, 13):
                if (ano == fecha_ultimo_pago.year and mes < fecha_ultimo_pago.month) or (ano == hoy.year and mes > hoy.month):
                    continue
                meses_totales.add((ano, mes))

        # Crear un conjunto de los meses que ya han sido pagados
        meses_pagados = set()
        for pago in pagos:
            mes_pago = pago.Mes.upper().strip()  # Normalizamos el mes
            if mes_pago in meses_map:
                ano_pago = pago.Ano
                meses_pagados.add((ano_pago, meses_map[mes_pago]))

        # Identificar los meses de deuda (diferencia entre los meses totales y los pagados)
        meses_deuda = meses_totales - meses_pagados

        # Asegurarse de contar solo los meses vencidos con respecto al día de corte
        meses_deuda_filtrados = {
            (ano, mes) for (ano, mes) in meses_deuda if (ano < hoy.year or (ano == hoy.year and mes < hoy.month) or (ano == hoy.year and mes == hoy.month and hoy.day >= dia_corte))
        }

        # Si el cliente debe más meses de los seleccionados, calcular la deuda
        if len(meses_deuda_filtrados) >= meses_deuda_minima:
            total_deuda = len(meses_deuda_filtrados) * cliente.Tarifa
            tipo_servicio = session.query(TipoServicio).filter_by(ID=cliente.TipoServicioID).first().Tipo
            clientes_morosos.append({
                'ID': cliente.ID,
                'Nombre': cliente.NombreCliente,
                'Telefono': cliente.Telefono,
                'Ubicacion': cliente.Ubicacion,
                'Fecha de Instalación': cliente.FechaInstalacion,
                'Meses Deuda': len(meses_deuda_filtrados),
                'Monto Deuda': total_deuda,
                'Tipo de Servicio': tipo_servicio
            })

    # Mostrar los resultados
    if clientes_morosos:
        df_morosos = pd.DataFrame(clientes_morosos)

        # Mostrar la tabla con la fecha de instalación y tipo de servicio incluidos
        st.write(df_morosos.to_html(escape=False), unsafe_allow_html=True)

        # Descargar solo la tabla mostrada
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_morosos.to_excel(writer, index=False, sheet_name='Morosos')
        output.seek(0)

        st.download_button(
            label="Descargar morosos en Excel",
            data=output,
            file_name='clientes_morosos.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            key='download_morosos'
        )
    else:
        st.write(f"No hay clientes con deuda de {meses_deuda_minima} mes(es) o más.")

def agregar_pago():
    st.subheader('Agregar Pago')
    buscar_por = st.selectbox('Buscar cliente por', ['Nombre', 'Cedula'], key='buscar_pago_por')
    buscar_valor = st.text_input(f'Valor para buscar {buscar_por}', key='buscar_pago_valor').lower()

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
            estado_cliente = session.query(Estado).filter_by(ID=cliente.EstadoID).first().Estado
            st.write(f'Cliente seleccionado: {cliente.NombreCliente}, ID: {cliente.ID}')
            st.write(f'Fecha de Instalación: {cliente.FechaInstalacion}')
            st.write(f'Estado: {estado_cliente}')
            
            pagos = session.query(Pago).filter_by(ClienteID=cliente.ID).all()
            if pagos:
                pagos_data = []
                for pago in pagos:
                    metodo_pago = session.query(MetodoDePago).filter_by(ID=pago.Metodo_de_PagoID).first()
                    metodo_pago_nombre = metodo_pago.Metodo if metodo_pago else 'Desconocido'
                    pagos_data.append({
                        'ID': pago.ID,
                        'Fecha de Pago': pago.FechaPago,
                        'Mes': pago.Mes,
                        'Año': pago.Ano,
                        'Monto': pago.Monto,
                        'Método de Pago': metodo_pago_nombre
                    })
                df_pagos = pd.DataFrame(pagos_data)
                st.write(df_pagos.to_html(escape=False), unsafe_allow_html=True)
            else:
                st.write('No hay pagos registrados para este cliente.')

            fecha_pago = st.date_input('Fecha de Pago', date.today(), key='fecha_pago')
            mes_pago = st.selectbox('Mes de Pago', list(meses_map.keys()), key='mes_pago')
            ano_pago = st.number_input('Año de Pago', min_value=2020, value=date.today().year, key='ano_pago')
            monto_pago = st.number_input('Monto de Pago', min_value=0.0, key='monto_pago')
            metodo_pago = st.selectbox('Método de Pago', session.query(MetodoDePago).all(), format_func=lambda x: x.Metodo, key='metodo_pago')

            if st.button('Agregar Pago'):
                nuevo_pago = Pago(
                    ClienteID=cliente.ID,
                    FechaPago=fecha_pago,
                    Mes=mes_pago,
                    Ano=ano_pago,
                    Monto=monto_pago,
                    Metodo_de_PagoID=metodo_pago.ID
                )
                session.add(nuevo_pago)
                session.commit()
                st.success('Pago agregado exitosamente')
                del st.session_state.cliente_seleccionado
                st.experimental_rerun()

# Verificar si el usuario ya está autenticado
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if st.session_state.logged_in:
    st.sidebar.title("Navegación")
    
    # Agregar opción en la barra lateral para la prueba
    opciones = st.sidebar.radio("Ir a", [
        "Dashboard", 
        "Crear Usuario", 
        "Buscar Cliente", 
        "Agregar Cliente", 
        "Editar Cliente", 
        "Mostrar Morosos", 
        "Agregar Pago", 
    ])

    # Obtener datos de clientes
    clientes = session.query(Cliente).all()
    cliente_data = [
        {
            'ID': cliente.ID,
            'Nombre': cliente.NombreCliente,
            'Plan': cliente.PlanMB,
            'Fecha Instalacion': cliente.FechaInstalacion,
            'Tipo de Servicio': session.query(TipoServicio).filter_by(ID=cliente.TipoServicioID).first().Tipo,
            'Tarifa': cliente.Tarifa,
            'IP Address': cliente.IPAddress,
            'Telefono': cliente.Telefono,
            'Ubicacion': cliente.Ubicacion,
            'Cedula': cliente.Cedula,
            'Estado': session.query(Estado).filter_by(ID=cliente.EstadoID).first().Estado
        } for cliente in clientes
    ]

    # Definir el DataFrame antes de usarlo
    df_clientes = pd.DataFrame(cliente_data)

    # Definir la acción según la opción seleccionada en la navegación
    if opciones == "Dashboard":
        dashboard()
    
    elif opciones == "Crear Usuario":
        crear_usuario()

    elif opciones == "Buscar Cliente":
        # Asegúrate de que df_clientes está definida antes de usarla
        buscar_cliente(df_clientes)

    elif opciones == "Agregar Cliente":
        agregar_cliente()

    elif opciones == "Editar Cliente":
        editar_cliente()

    elif opciones == "Mostrar Morosos":
        mostrar_morosos()

    elif opciones == "Agregar Pago":
        agregar_pago()

    session.close()
else:
    login()
