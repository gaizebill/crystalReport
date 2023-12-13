import pandas as pd
from datetime import datetime
import streamlit as st
import os

# Función para mapear los estados de tu reporte a los estados de Crystal
def map_status(status):
    status_mapping = {
        "En Terminal Origen": [
            "new",
            "estimating",
            "estimating_failed",
            "ready_for_approval",
            "accepted"
        ],
        "En Terminal Destino": [
            "performer_lookup",
            "performer_draft",
            "performer_found",
            "performer_not_found",
            "pickup_arrived",
            "ready_for_pickup_confirmation"
        ],
        "En Transporte": [
            "pickuped"
        ],
        "En Reparto": [
            "delivery_arrived",
            "ready_for_delivery_confirmation",
            "pay_waiting",
            "returned",
            "returned_finish"
        ],
        "Entregada": [
            "delivered",
            "delivered_finish"
        ],
        "Cerrado Por Incidencia": [
            "failed",
            "cancelled",
            "cancelled_with_payment",
            "cancelled_by_taxi",
            "cancelled_with_items_on_hands"
        ]
    }
    for crystal_status, streamlit_statuses in status_mapping.items():
        if status in streamlit_statuses:
            return crystal_status
    return "Estado no mapeado"  # Si no encuentra un mapeo, devuelve un estado predeterminado

# Función para procesar el archivo seleccionado
def process_file(selected_file):
    try:
        # Leer el reporte de Streamlit directamente desde el objeto de archivo
        data_streamlit = pd.read_excel(selected_file)

        # Crear un DataFrame para el reporte de Crystal
        report_crystal = pd.DataFrame()

        # Mapear las columnas del reporte de Streamlit a las del reporte de Crystal
        report_crystal['NumeroRemesa'] = data_streamlit['client_id']
        report_crystal['FechaRemesa'] = data_streamlit['cutoff'].apply(convert_cutoff_date)
        mapped_status = data_streamlit['status'].apply(map_status)
        report_crystal['EstadoRemesa'] = mapped_status
        report_crystal['TieneNovedad'] = mapped_status.apply(lambda x: 1 if x == "Entregada" else "")
        report_crystal['DescripcionNovedad'] = mapped_status.apply(lambda x: "Entrega se realiza cita destinatario" if x == "Entregada" else "")
        report_crystal['UnidadNegocio'] = "Mercancia"
        report_crystal['FechaEntrega'] = data_streamlit.apply(lambda row: convert_status_time(row['status_time']) if map_status(row['status']) == "Entregada" else "", axis=1)
        report_crystal['NumeroDocumento'] = 1
        report_crystal['Remitente'] = "Crystal"

        # Asignar valores de las columnas 'pickup_address' y 'receiver_address'
        report_crystal['Origen'] = data_streamlit['pickup_address']
        report_crystal['Destino'] = data_streamlit['receiver_address']

        # Agregar columnas vacías
        empty_columns = ['Destinatario', 'TelefonoDestinatario', 'CuentaRemitente',
                         'TotalUnidades', 'KilosReales', 'ObservacionesRemesa', 'EstadoNovedad', 'TipoVinculo', 
                         'GuiaNueva', 'FechaPrimeraVisita', 'HoraPrimeraVisita']
        for col in empty_columns:
            report_crystal[col] = ""

        # Crear un botón para descargar el archivo CSV
        st.download_button(
            label="Descargar Reporte CSV",
            data=report_crystal.to_csv(index=False, sep=';'),
            file_name=f"{selected_file.name}_transformed.csv",
            key="csv-download-button"
        )

        st.success("El reporte ha sido transformado y se encuentra listo para descargar.")

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo: {e}")

# Función para convertir la fecha de corte
def convert_cutoff_date(cutoff):
    try:
        return datetime.strptime(cutoff, "%Y-%m-%d %H:%M").strftime('%Y/%m/%d')
    except ValueError as e:
        st.error(f"Formato de fecha de corte no válido: {e}")
        return None

# Función para convertir la hora de estado
def convert_status_time(status_time):
    try:
        # Remover la 'T' y la parte de microsegundos, además de la zona horaria
        clean_time = status_time.replace('T', ' ').split('.')[0]
        return datetime.strptime(clean_time, "%Y-%m-%d %H:%M:%S").strftime('%Y/%m/%d %H:%M:%S')
    except ValueError as e:
        st.error(f"Formato de hora de estado no válido: {e}")
        return None

# Configurar la aplicación de Streamlit
st.title("Procesador de Reportes")

# Botón para seleccionar el archivo
selected_file = st.file_uploader("Seleccionar Archivo Excel", type=["xlsx"])
if selected_file:
    st.success(f"Se ha seleccionado el archivo: {selected_file.name}")

# Botón para procesar el archivo
if selected_file and st.button("Procesar Archivo", key="process-button"):
    process_file(selected_file)
elif not selected_file and st.button("Procesar Archivo sin Clave Única", key="process-button-warning"):
    st.warning("Por favor, selecciona un archivo primero.")
