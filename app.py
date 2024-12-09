import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Date, Boolean, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.dialects.mysql import LONGBLOB
import pandas as pd
import base64
from PIL import Image
import io
from datetime import datetime
from streamlit_option_menu import option_menu
import os

Base = declarative_base()

# Database credentials
db_user = st.secrets['DB_USER']
db_password = st.secrets['DB_PASSWORD']
db_host = st.secrets['DB_HOST']
db_port = st.secrets['DB_PORT']
db_name = st.secrets['DB_NAME']

class Product(Base):
    __tablename__ = 'product'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    quantity = Column(Float, default=0.0, nullable=False)
    unit = Column(String(20), nullable=False, default='stk')

class Material(Base):
    __tablename__ = 'material'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    producer_name = Column(String(80), nullable=True)
    unit = Column(String(20), nullable=False)
    quantity = Column(Float, default=0.0, nullable=False)

class Customer(Base):
    __tablename__ = 'customer'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    address = Column(String(120), nullable=False)
    contact_email = Column(String(80), nullable=False)
    phone_number = Column(String(20), nullable=False)
    vat_number = Column(String(20), nullable=False)

class Supplier(Base):
    __tablename__ = 'supplier'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    address = Column(String(120), nullable=False)
    contact_email = Column(String(80), nullable=False)
    phone_number = Column(String(20), nullable=False)
    vat_number = Column(String(20), nullable=False)
    organic_number = Column(String(80), nullable=True)
    report_file = Column(LONGBLOB, nullable=True)
    report_filename = Column(String(255), nullable=True)
    report_mimetype = Column(String(50), nullable=True)

class Recipe(Base):
    __tablename__ = 'recipe'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('product.id'), nullable=False)
    method = Column(Text, nullable=True)
    output_quantity = Column(Float, nullable=False)

class BoM(Base):
    __tablename__ = 'bom'
    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey('recipe.id'), nullable=False)
    component_material_id = Column(Integer, ForeignKey('material.id'), nullable=True)
    component_product_id = Column(Integer, ForeignKey('product.id'), nullable=True)
    quantity_required = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)

class ProductionOrder(Base):
    __tablename__ = 'production_order'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('product.id'), nullable=False)
    quantity = Column(Float, nullable=False)
    status = Column(String(20), default='Afventer', nullable=False)
    batch_id = Column(String(80), nullable=False)
    date = Column(Date, nullable=False)

class ProductionOrderComponent(Base):
    __tablename__ = 'production_order_component'
    id = Column(Integer, primary_key=True)
    production_order_id = Column(Integer, ForeignKey('production_order.id'), nullable=False)
    component_material_id = Column(Integer, ForeignKey('material.id'), nullable=True)
    component_product_id = Column(Integer, ForeignKey('product.id'), nullable=True)
    batch_id = Column(Integer, nullable=False)
    quantity_used = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)

class SalesOrder(Base):
    __tablename__ = 'sales_order'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('product.id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customer.id'), nullable=False)
    quantity = Column(Float, nullable=False)
    status = Column(String(20), default='Afventer', nullable=False)
    date = Column(Date, nullable=False)

class MaterialBatch(Base):
    __tablename__ = 'material_batch'
    id = Column(Integer, primary_key=True)
    material_id = Column(Integer, ForeignKey('material.id'), nullable=False)
    batch_id = Column(String(80), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    date = Column(Date, nullable=False)
    checked = Column(Boolean, default=False, nullable=False)

class ProductBatch(Base):
    __tablename__ = 'product_batch'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('product.id'), nullable=False)
    batch_id = Column(String(80), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    date = Column(Date, nullable=False)

class DisposalRecord(Base):
    __tablename__ = 'disposal_record'
    id = Column(Integer, primary_key=True)
    material_id = Column(Integer, ForeignKey('material.id'), nullable=True)
    product_id = Column(Integer, ForeignKey('product.id'), nullable=True)
    batch_id = Column(Integer, nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    reason = Column(String(255), nullable=False)
    date = Column(Date, nullable=False)

class PurchaseOrder(Base):
    __tablename__ = 'purchase_order'
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey('supplier.id'), nullable=False)
    date = Column(Date, nullable=False)
    checked = Column(Boolean, default=False, nullable=False)
    invoice_file = Column(LONGBLOB, nullable=True)
    invoice_filename = Column(String(255), nullable=True)
    invoice_mimetype = Column(String(50), nullable=True)
    items = relationship('PurchaseOrderItem', backref='purchase_order')

class PurchaseOrderItem(Base):
    __tablename__ = 'purchase_order_item'
    id = Column(Integer, primary_key=True)
    purchase_order_id = Column(Integer, ForeignKey('purchase_order.id'), nullable=False)
    material_id = Column(Integer, ForeignKey('material.id'), nullable=False)
    batch_id = Column(String(80), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)

cert_path = os.path.join(os.path.dirname(__file__), "certs", "DigiCertGlobalRootCA.crt.pem")
if not os.path.exists(cert_path):
    st.error("Certificate file not found. Please verify the path.")

engine = create_engine(
    f'mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}',
    connect_args={
        'ssl': {
            'ssl_ca': cert_path
        }
    }
)
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)
session = DBSession()

st.set_page_config(layout="wide")

# Caching functions
@st.cache_data(show_spinner=False)
def get_all_materials():
    return session.query(Material).all()

@st.cache_data(show_spinner=False)
def get_all_products():
    return session.query(Product).all()

@st.cache_data(show_spinner=False)
def get_all_customers():
    return session.query(Customer).all()

@st.cache_data(show_spinner=False)
def get_all_suppliers():
    return session.query(Supplier).all()

@st.cache_data(show_spinner=False)
def get_all_boms():
    return session.query(BoM).all()

@st.cache_data(show_spinner=False)
def get_all_production_orders():
    return session.query(ProductionOrder).all()

@st.cache_data(show_spinner=False)
def get_all_sales_orders():
    return session.query(SalesOrder).all()

@st.cache_data(show_spinner=False)
def get_all_purchase_orders():
    return session.query(PurchaseOrder).all()

@st.cache_data(show_spinner=False)
def get_all_material_batches():
    return session.query(MaterialBatch).all()

@st.cache_data(show_spinner=False)
def get_all_product_batches():
    return session.query(ProductBatch).all()

def refresh_materials():
    get_all_materials.clear()
    st.session_state.materials = get_all_materials()

def refresh_products():
    get_all_products.clear()
    st.session_state.products = get_all_products()

def refresh_customers():
    get_all_customers.clear()
    st.session_state.customers = get_all_customers()

def refresh_suppliers():
    get_all_suppliers.clear()
    st.session_state.suppliers = get_all_suppliers()

def refresh_boms():
    get_all_boms.clear()
    st.session_state.boms = get_all_boms()

def refresh_production_orders():
    get_all_production_orders.clear()
    st.session_state.production_orders = get_all_production_orders()

def refresh_sales_orders():
    get_all_sales_orders.clear()
    st.session_state.sales_orders = get_all_sales_orders()

def refresh_purchase_orders():
    get_all_purchase_orders.clear()
    st.session_state.purchase_orders = get_all_purchase_orders()

def refresh_material_batches():
    get_all_material_batches.clear()
    st.session_state.material_batches = get_all_material_batches()

def refresh_product_batches():
    get_all_product_batches.clear()
    st.session_state.product_batches = get_all_product_batches()

def convert_units(quantity, from_unit, to_unit):
    conversion_factors = {
        ('kg', 'g'): 1000,
        ('g', 'kg'): 0.001,
        ('l', 'ml'): 1000,
        ('ml', 'l'): 0.001,
    }
    if from_unit == to_unit:
        return quantity
    return quantity * conversion_factors.get((from_unit, to_unit), 1)

# Initialize session state
if "materials" not in st.session_state:
    st.session_state.materials = get_all_materials()

if "products" not in st.session_state:
    st.session_state.products = get_all_products()

if "customers" not in st.session_state:
    st.session_state.customers = get_all_customers()

if "suppliers" not in st.session_state:
    st.session_state.suppliers = get_all_suppliers()

if "boms" not in st.session_state:
    st.session_state.boms = get_all_boms()

if "production_orders" not in st.session_state:
    st.session_state.production_orders = get_all_production_orders()

if "sales_orders" not in st.session_state:
    st.session_state.sales_orders = get_all_sales_orders()

if "purchase_orders" not in st.session_state:
    st.session_state.purchase_orders = get_all_purchase_orders()

if "material_batches" not in st.session_state:
    st.session_state.material_batches = get_all_material_batches()

if "product_batches" not in st.session_state:
    st.session_state.product_batches = get_all_product_batches()

with st.sidebar:
    st.title("ERP System")
    st.header("Handlinger")
    action = option_menu(
        menu_title=None,
        options=[
            "Opret et nyt materiale", "Køb noget", "Producer noget", "Opret en ny opskrift / stykliste",
            "Sælg noget", "Flyt noget", "Smid noget ud", "Opret en ny kunde", "Opret en ny leverandør", "Administrationsside"
        ],
        icons=[
            "file-plus", "cart-plus", "gear", "clipboard",
            "cart", "arrows-move", "trash", "person-plus", "truck", "tools"
        ],
        menu_icon="cast",
        default_index=0,
    )

st.header("ERP System")

if action == "Administrationsside":
    st.header("Administrationsside")
    management_option = st.selectbox(
        "Vælg, hvad du vil administrere",
        ["Materialer", "Produkter", "Kunder", "Leverandører", "Styklister (BoM)", "Produktionsordrer", "Salgsordrer", "Indkøbsordrer", "Materiale Batches", "Produkt Batches"]
    )

    # Manage Materials
    if management_option == "Materialer":
        materials = session.query(Material).all()
        material_options = [(m.id, m.name, m.quantity, m.unit, m.producer_name) for m in materials]
        df = pd.DataFrame(material_options, columns=["ID", "Navn", "Mængde", "Enhed", "Producentnavn"])
        st.dataframe(df)

        st.subheader("Rediger eller slet materiale")
        selected_material_id = st.number_input("Indtast materiale ID", min_value=1, step=1, key="selected_material_id")
        selected_material = session.query(Material).filter_by(id=selected_material_id).first()
        if selected_material:
            new_name = st.text_input("Materialets navn", value=selected_material.name)
            new_unit = st.selectbox("Enhed", ["kg", "g", "l", "ml", "stk"], index=["kg", "g", "l", "ml", "stk"].index(selected_material.unit))
            new_quantity = st.number_input("Mængde", min_value=0.0, step=0.1, value=selected_material.quantity)
            new_producer_name = st.text_input("Producentnavn", value=selected_material.producer_name or "")

            if st.button("Opdater materiale"):
                selected_material.name = new_name
                selected_material.unit = new_unit
                selected_material.quantity = new_quantity
                selected_material.producer_name = new_producer_name
                try:
                    session.commit()
                    refresh_materials()
                    st.success("Materiale opdateret med succes!")
                except Exception as e:
                    session.rollback()
                    st.error(f"Fejl under opdatering af materiale: {str(e)}")

            if st.button("Slet materiale"):
                confirm_delete = st.checkbox("Bekræft sletning")
                if confirm_delete:
                    try:
                        bom_entries = session.query(BoM).filter_by(component_material_id=selected_material_id).all()
                        if bom_entries:
                            st.error("Kan ikke slette materialet, da det bruges i en stykliste.")
                        else:
                            material_batches = session.query(MaterialBatch).filter_by(material_id=selected_material_id).all()
                            if material_batches:
                                st.error("Kan ikke slette materialet, da der er tilknyttede batches.")
                            else:
                                session.delete(selected_material)
                                session.commit()
                                refresh_materials()
                                st.success("Materiale slettet med succes!")
                    except Exception as e:
                        session.rollback()
                        st.error(f"Fejl under sletning af materiale: {str(e)}")
                else:
                    st.warning("Marker 'Bekræft sletning' for at slette materialet.")
        else:
            st.info("Indtast et gyldigt materiale ID for at redigere eller slette.")

    elif management_option == "Produkter":
        products = session.query(Product).all()
        product_options = [(p.id, p.name, p.quantity, p.unit) for p in products]
        df = pd.DataFrame(product_options, columns=["ID", "Navn", "Mængde", "Enhed"])
        st.dataframe(df)

        st.subheader("Rediger eller slet produkt")
        selected_product_id = st.number_input("Indtast produkt ID", min_value=1, step=1, key="selected_product_id")
        selected_product = session.query(Product).filter_by(id=selected_product_id).first()
        if selected_product:
            new_name = st.text_input("Produktnavn", value=selected_product.name)
            new_unit = st.selectbox("Enhed", ["kg", "g", "l", "ml", "stk"], index=["kg", "g", "l", "ml", "stk"].index(selected_product.unit))
            new_quantity = st.number_input("Mængde", min_value=0.0, step=0.1, value=selected_product.quantity)

            if st.button("Opdater produkt"):
                selected_product.name = new_name
                selected_product.unit = new_unit
                selected_product.quantity = new_quantity
                try:
                    session.commit()
                    refresh_products()
                    st.success("Produkt opdateret med succes!")
                except Exception as e:
                    session.rollback()
                    st.error(f"Fejl under opdatering af produkt: {str(e)}")

            if st.button("Slet produkt"):
                confirm_delete = st.checkbox("Bekræft sletning")
                if confirm_delete:
                    try:
                        bom_entries = session.query(BoM).filter(
                            (BoM.component_product_id == selected_product_id) | (BoM.recipe_id == selected_product_id)
                        ).all()
                        production_orders = session.query(ProductionOrder).filter_by(product_id=selected_product_id).all()
                        if bom_entries or production_orders:
                            st.error("Kan ikke slette produktet, da det bruges i en stykliste eller produktionsordre.")
                        else:
                            product_batches = session.query(ProductBatch).filter_by(product_id=selected_product_id).all()
                            if product_batches:
                                st.error("Kan ikke slette produktet, da der er tilknyttede batches.")
                            else:
                                session.delete(selected_product)
                                session.commit()
                                refresh_products()
                                st.success("Produkt slettet med succes!")
                    except Exception as e:
                        session.rollback()
                        st.error(f"Fejl under sletning af produkt: {str(e)}")
                else:
                    st.warning("Marker 'Bekræft sletning' for at slette produktet.")
        else:
            st.info("Indtast et gyldigt produkt ID for at redigere eller slette.")

    elif management_option == "Kunder":
        customers = session.query(Customer).all()
        customer_options = [(c.id, c.name, c.address, c.contact_email, c.phone_number, c.vat_number) for c in customers]
        df = pd.DataFrame(customer_options, columns=["ID", "Navn", "Adresse", "Kontakt Email", "Telefonnummer", "CVR-nummer"])
        st.dataframe(df)

        st.subheader("Rediger eller slet kunde")
        selected_customer_id = st.number_input("Indtast kunde ID", min_value=1, step=1, key="selected_customer_id")
        selected_customer = session.query(Customer).filter_by(id=selected_customer_id).first()
        if selected_customer:
            new_name = st.text_input("Kundens navn", value=selected_customer.name)
            new_address = st.text_input("Kundens adresse", value=selected_customer.address)
            new_contact_email = st.text_input("Kontakt email", value=selected_customer.contact_email)
            new_phone_number = st.text_input("Telefonnummer", value=selected_customer.phone_number)
            new_vat_number = st.text_input("CVR-nummer", value=selected_customer.vat_number)

            if st.button("Opdater kunde"):
                selected_customer.name = new_name
                selected_customer.address = new_address
                selected_customer.contact_email = new_contact_email
                selected_customer.phone_number = new_phone_number
                selected_customer.vat_number = new_vat_number
                try:
                    session.commit()
                    refresh_customers()
                    st.success("Kunde opdateret med succes!")
                except Exception as e:
                    session.rollback()
                    st.error(f"Fejl under opdatering af kunde: {str(e)}")

            if st.button("Slet kunde"):
                confirm_delete = st.checkbox("Bekræft sletning")
                if confirm_delete:
                    try:
                        sales_orders = session.query(SalesOrder).filter_by(customer_id=selected_customer_id).all()
                        if sales_orders:
                            st.error("Kan ikke slette kunden, da der er tilknyttede salgsordrer.")
                        else:
                            session.delete(selected_customer)
                            session.commit()
                            refresh_customers()
                            st.success("Kunde slettet med succes!")
                    except Exception as e:
                        session.rollback()
                        st.error(f"Fejl under sletning af kunde: {str(e)}")
                else:
                    st.warning("Marker 'Bekræft sletning' for at slette kunden.")
        else:
            st.info("Indtast et gyldigt kunde ID for at redigere eller slette.")

    elif management_option == "Leverandører":
        suppliers = session.query(Supplier).all()
        supplier_options = [(s.id, s.name, s.address, s.contact_email, s.phone_number, s.vat_number, s.organic_number) for s in suppliers]
        df = pd.DataFrame(supplier_options, columns=["ID", "Navn", "Adresse", "Kontakt Email", "Telefonnummer", "CVR-nummer", "Økologinummer"])
        st.dataframe(df)

        st.subheader("Rediger eller slet leverandør")
        selected_supplier_id = st.number_input("Indtast leverandør ID", min_value=1, step=1, key="selected_supplier_id")
        selected_supplier = session.query(Supplier).filter_by(id=selected_supplier_id).first()
        if selected_supplier:
            new_name = st.text_input("Leverandørens navn", value=selected_supplier.name)
            new_address = st.text_input("Leverandørens adresse", value=selected_supplier.address)
            new_contact_email = st.text_input("Kontakt email", value=selected_supplier.contact_email)
            new_phone_number = st.text_input("Telefonnummer", value=selected_supplier.phone_number)
            new_vat_number = st.text_input("CVR-nummer", value=selected_supplier.vat_number)
            new_organic_number = st.text_input("Økologinummer", value=selected_supplier.organic_number or "")

            report_file = st.file_uploader("Upload ny leverandørrapport (PDF eller billede)", type=["pdf", "png", "jpg", "jpeg"], key="edit_supplier_report")
            report_file_data = selected_supplier.report_file
            report_filename = selected_supplier.report_filename
            report_mimetype = selected_supplier.report_mimetype
            if report_file is not None:
                report_file_data = report_file.read()
                report_filename = report_file.name
                report_mimetype = report_file.type

            if st.button("Opdater leverandør"):
                selected_supplier.name = new_name
                selected_supplier.address = new_address
                selected_supplier.contact_email = new_contact_email
                selected_supplier.phone_number = new_phone_number
                selected_supplier.vat_number = new_vat_number
                selected_supplier.organic_number = new_organic_number
                selected_supplier.report_file = report_file_data
                selected_supplier.report_filename = report_filename
                selected_supplier.report_mimetype = report_mimetype
                try:
                    session.commit()
                    refresh_suppliers()
                    st.success("Leverandør opdateret med succes!")
                except Exception as e:
                    session.rollback()
                    st.error(f"Fejl under opdatering af leverandør: {str(e)}")

            if selected_supplier.report_file:
                st.write("**Leverandørrapport:**")
                if selected_supplier.report_mimetype == 'application/pdf':
                    b64_pdf = base64.b64encode(selected_supplier.report_file).decode('utf-8')
                    pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)
                elif selected_supplier.report_mimetype and selected_supplier.report_mimetype.startswith('image/'):
                    image = Image.open(io.BytesIO(selected_supplier.report_file))
                    st.image(image)
                else:
                    st.download_button("Download rapport", data=selected_supplier.report_file, file_name=selected_supplier.report_filename, mime=selected_supplier.report_mimetype)
            else:
                st.write("Ingen leverandørrapport uploadet.")
        else:
            st.info("Indtast et gyldigt leverandør ID for at redigere eller slette.")

    elif management_option == "Styklister (BoM)":
        boms = session.query(BoM).all()
        products = session.query(Product).all()
        product_map = {p.id: p for p in products}
        recipes = session.query(Recipe).all()
        recipe_map = {r.id: r for r in recipes}
        materials = session.query(Material).all()
        material_map = {m.id: m for m in materials}
        bom_options = []
        for b in boms:
            recipe = recipe_map.get(b.recipe_id)
            if recipe:
                product = product_map.get(recipe.product_id)
            else:
                product = None
            if b.component_material_id:
                component = material_map.get(b.component_material_id)
                component_name = component.name if component else "Ukendt"
                component_type = "Materiale"
            elif b.component_product_id:
                comp_product = product_map.get(b.component_product_id)
                component_name = comp_product.name if comp_product else "Ukendt"
                component_type = "Produkt"
            else:
                component_name = "Ukendt"
                component_type = "Ukendt"
            product_name = product.name if product else "Ukendt"
            bom_options.append((b.id, product_name, component_type, component_name, b.quantity_required, b.unit))
        df = pd.DataFrame(bom_options, columns=["ID", "Produkt", "Komponenttype", "Komponentnavn", "Krævet Mængde", "Enhed"])
        st.dataframe(df)

        st.subheader("Slet styklistepost")
        selected_bom_id = st.number_input("Indtast stykliste ID", min_value=1, step=1, key="selected_bom_id")
        selected_bom = session.query(BoM).filter_by(id=selected_bom_id).first()
        if selected_bom:
            if st.button("Slet styklistepost"):
                confirm_delete = st.checkbox("Bekræft sletning")
                if confirm_delete:
                    try:
                        session.delete(selected_bom)
                        session.commit()
                        refresh_boms()
                        st.success("Styklistepost slettet med succes!")
                    except Exception as e:
                        session.rollback()
                        st.error(f"Fejl under sletning af styklistepost: {str(e)}")
                else:
                    st.warning("Marker 'Bekræft sletning' for at slette styklisteposten.")
        else:
            st.info("Indtast et gyldigt stykliste ID for at slette.")

    elif management_option == "Produktionsordrer":
        production_orders = session.query(ProductionOrder).all()
        products = session.query(Product).all()
        product_map = {p.id: p for p in products}
        production_data = []
        for po in production_orders:
            product = product_map.get(po.product_id, None)
            production_data.append({
                "ID": po.id,
                "Produkt": product.name if product else "Ukendt",
                "Mængde": po.quantity,
                "Batch ID": po.batch_id,
                "Dato": po.date.strftime("%Y-%m-%d"),
                "Status": po.status
            })
        df = pd.DataFrame(production_data)
        st.dataframe(df)

        st.subheader("Rediger eller slet produktionsordre")
        selected_production_order_id = st.number_input("Indtast produktionsordre ID", min_value=1, step=1, key="selected_production_order_id")
        selected_order = session.query(ProductionOrder).filter_by(id=selected_production_order_id).first()
        if selected_order:
            new_status = st.selectbox("Status", ["Afventer", "Planlagt", "I gang", "Afsluttet", "Annulleret"], index=["Afventer", "Planlagt", "I gang", "Afsluttet", "Annulleret"].index(selected_order.status))
            new_quantity = st.number_input("Ny mængde af produkt", min_value=0.0, step=0.1, value=selected_order.quantity)
            product_options = [(p.id, p.name) for p in products]
            selected_product_index = next((index for (index, p) in enumerate(product_options) if p[0] == selected_order.product_id), 0)
            new_product_option = st.selectbox("Vælg nyt produkt", product_options, index=selected_product_index)
            new_product_id = new_product_option[0]

            if st.button("Opdater produktionsordre"):
                try:
                    old_product = session.query(Product).filter_by(id=selected_order.product_id).first()
                    old_product.quantity -= selected_order.quantity
                    new_product = session.query(Product).filter_by(id=new_product_id).first()
                    new_product.quantity += new_quantity
                    selected_order.status = new_status
                    selected_order.quantity = new_quantity
                    selected_order.product_id = new_product_id
                    session.commit()
                    refresh_products()
                    refresh_production_orders()
                    st.success("Produktionsordre opdateret med succes!")
                except Exception as e:
                    session.rollback()
                    st.error(f"Fejl under opdatering af produktionsordre: {str(e)}")

            if st.button("Slet produktionsordre"):
                confirm_delete = st.checkbox("Bekræft sletning")
                if confirm_delete:
                    try:
                        db_order = session.query(ProductionOrder).filter_by(id=selected_production_order_id).first()
                        product = session.query(Product).filter_by(id=db_order.product_id).first()
                        product.quantity -= db_order.quantity
                        product_batch = session.query(ProductBatch).filter_by(batch_id=db_order.batch_id).first()
                        if product_batch:
                            session.delete(product_batch)
                        components_used = session.query(ProductionOrderComponent).filter_by(production_order_id=selected_production_order_id).all()
                        for component in components_used:
                            if component.component_material_id:
                                material = session.query(Material).filter_by(id=component.component_material_id).first()
                                batch = session.query(MaterialBatch).filter_by(id=component.batch_id).first()
                                batch.quantity += component.quantity_used
                                material.quantity += convert_units(component.quantity_used, component.unit, material.unit)
                            else:
                                product_comp = session.query(Product).filter_by(id=component.component_product_id).first()
                                batch = session.query(ProductBatch).filter_by(id=component.batch_id).first()
                                batch.quantity += component.quantity_used
                                product_comp.quantity += convert_units(component.quantity_used, component.unit, product_comp.unit)
                            session.delete(component)
                        session.delete(db_order)
                        session.commit()
                        refresh_materials()
                        refresh_products()
                        refresh_production_orders()
                        refresh_product_batches()
                        st.success("Produktionsordre slettet og lager opdateret med succes!")
                    except Exception as e:
                        session.rollback()
                        st.error(f"Fejl under sletning af produktionsordre: {str(e)}")
                else:
                    st.warning("Marker 'Bekræft sletning' for at slette produktionsordren.")
        else:
            st.info("Indtast et gyldigt produktionsordre ID for at redigere eller slette.")

    elif management_option == "Salgsordrer":
        sales_orders = session.query(SalesOrder).all()
        products = st.session_state.products
        product_map = {p.id: p for p in products}
        customers = st.session_state.customers
        customer_map = {c.id: c for c in customers}
        sales_data = []
        for so in sales_orders:
            product = product_map.get(so.product_id)
            customer = customer_map.get(so.customer_id)
            sales_data.append({
                "ID": so.id,
                "Produkt": product.name if product else "Ukendt",
                "Kunde": customer.name if customer else "Ukendt",
                "Mængde": so.quantity,
                "Dato": so.date.strftime("%Y-%m-%d"),
                "Status": so.status
            })
        df = pd.DataFrame(sales_data)
        st.dataframe(df)

        st.subheader("Rediger eller slet salgsordre")
        selected_sales_order_id = st.number_input("Indtast salgsordre ID", min_value=1, step=1, key="selected_sales_order_id")
        selected_order = session.query(SalesOrder).filter_by(id=selected_sales_order_id).first()
        if selected_order:
            new_status = st.selectbox("Status", ["Afventer", "Afsluttet", "Annulleret"], index=["Afventer", "Afsluttet", "Annulleret"].index(selected_order.status))
            if st.button("Opdater salgsordre"):
                selected_order.status = new_status
                try:
                    session.commit()
                    refresh_sales_orders()
                    st.success("Salgsordre opdateret med succes!")
                except Exception as e:
                    session.rollback()
                    st.error(f"Fejl under opdatering af salgsordre: {str(e)}")

            if st.button("Slet salgsordre"):
                confirm_delete = st.checkbox("Bekræft sletning")
                if confirm_delete:
                    try:
                        product = session.query(Product).filter_by(id=selected_order.product_id).first()
                        product.quantity += selected_order.quantity
                        session.delete(selected_order)
                        session.commit()
                        refresh_sales_orders()
                        refresh_products()
                        st.success("Salgsordre slettet og lager opdateret med succes!")
                    except Exception as e:
                        session.rollback()
                        st.error(f"Fejl under sletning af salgsordre: {str(e)}")
                else:
                    st.warning("Marker 'Bekræft sletning' for at slette salgsordren.")
        else:
            st.info("Indtast et gyldigt salgsordre ID for at redigere eller slette.")

    elif management_option == "Materiale Batches":
        material_batches = session.query(MaterialBatch).all()
        materials = st.session_state.materials
        material_map = {m.id: m for m in materials}
        batch_data = []
        for mb in material_batches:
            material = material_map.get(mb.material_id)
            batch_data.append({
                "ID": mb.id,
                "Materiale": material.name if material else "Ukendt",
                "Batch ID": mb.batch_id,
                "Mængde": mb.quantity,
                "Enhed": mb.unit,
                "Dato": mb.date.strftime("%Y-%m-%d"),
                "Tjekket": "Ja" if mb.checked else "Nej"
            })
        df = pd.DataFrame(batch_data)
        st.dataframe(df)

    elif management_option == "Produkt Batches":
        product_batches = session.query(ProductBatch).all()
        products = st.session_state.products
        product_map = {p.id: p for p in products}
        batch_data = []
        for pb in product_batches:
            product = product_map.get(pb.product_id)
            batch_data.append({
                "ID": pb.id,
                "Produkt": product.name if product else "Ukendt",
                "Batch ID": pb.batch_id,
                "Mængde": pb.quantity,
                "Enhed": pb.unit,
                "Dato": pb.date.strftime("%Y-%m-%d")
            })
        df = pd.DataFrame(batch_data)
        st.dataframe(df)

    elif management_option == "Indkøbsordrer":
        purchase_orders = session.query(PurchaseOrder).all()
        suppliers = st.session_state.suppliers
        supplier_map = {s.id: s for s in suppliers}
        po_data = []
        for po in purchase_orders:
            sup = supplier_map.get(po.supplier_id)
            po_data.append({
                "ID": po.id,
                "Leverandør": sup.name if sup else "Ukendt",
                "Dato": po.date.strftime("%Y-%m-%d"),
                "Tjekket": "Ja" if po.checked else "Nej"
            })
        df = pd.DataFrame(po_data)
        st.dataframe(df)
        selected_po_id = st.number_input("Indtast indkøbsordre ID", min_value=1, step=1, key="selected_po_id")
        selected_po = session.query(PurchaseOrder).filter_by(id=selected_po_id).first()
        if selected_po:
            sup = supplier_map.get(selected_po.supplier_id)
            st.write(f"**Leverandør:** {sup.name if sup else 'Ukendt'}")
            st.write(f"**Dato:** {selected_po.date}")
            st.write(f"**Tjekket:** {'Ja' if selected_po.checked else 'Nej'}")
            items = session.query(PurchaseOrderItem).filter_by(purchase_order_id=selected_po_id).all()
            materials = st.session_state.materials
            material_map = {m.id: m for m in materials}
            item_data = []
            for item in items:
                mat = material_map.get(item.material_id)
                item_data.append({
                    "Materiale": mat.name if mat else "Ukendt",
                    "Batch ID": item.batch_id,
                    "Mængde": item.quantity,
                    "Enhed": item.unit
                })
            item_df = pd.DataFrame(item_data)
            st.dataframe(item_df)
            if selected_po.invoice_file:
                st.write("**Faktura:**")
                if selected_po.invoice_mimetype == 'application/pdf':
                    b64_pdf = base64.b64encode(selected_po.invoice_file).decode('utf-8')
                    pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)
                elif selected_po.invoice_mimetype and selected_po.invoice_mimetype.startswith('image/'):
                    image = Image.open(io.BytesIO(selected_po.invoice_file))
                    st.image(image)
                else:
                    st.download_button("Download faktura", data=selected_po.invoice_file, file_name=selected_po.invoice_filename, mime=selected_po.invoice_mimetype)
            else:
                st.write("Ingen faktura uploadet.")
            suppliers_options = [(s.id, s.name) for s in suppliers]
            selected_supplier_index = next((index for (index, s) in enumerate(suppliers_options) if s[0] == selected_po.supplier_id), 0)
            new_supplier_id = st.selectbox("Vælg ny leverandør", suppliers_options, index=selected_supplier_index)
            new_date = st.date_input("Ny dato", value=selected_po.date)
            new_checked = st.checkbox("Vare modtaget og tjekket", value=selected_po.checked)
            invoice_file = st.file_uploader("Upload ny faktura (PDF eller billede)", type=["pdf", "png", "jpg", "jpeg"], key="edit_invoice_file")
            invoice_file_data = selected_po.invoice_file
            invoice_filename = selected_po.invoice_filename
            invoice_mimetype = selected_po.invoice_mimetype
            if invoice_file is not None:
                invoice_file_data = invoice_file.read()
                invoice_filename = invoice_file.name
                invoice_mimetype = invoice_file.type

            if st.button("Opdater indkøbsordre"):
                try:
                    db_po = session.query(PurchaseOrder).filter_by(id=selected_po_id).first()
                    db_po.supplier_id = new_supplier_id
                    db_po.date = new_date
                    db_po.checked = new_checked
                    db_po.invoice_file = invoice_file_data
                    db_po.invoice_filename = invoice_filename
                    db_po.invoice_mimetype = invoice_mimetype
                    session.commit()
                    refresh_purchase_orders()
                    st.success("Indkøbsordre opdateret med succes!")
                except Exception as e:
                    session.rollback()
                    st.error(f"Fejl under opdatering af indkøbsordre: {str(e)}")

            if st.button("Slet indkøbsordre"):
                confirm_delete = st.checkbox("Bekræft sletning")
                if confirm_delete:
                    try:
                        db_po = session.query(PurchaseOrder).filter_by(id=selected_po_id).first()
                        items = session.query(PurchaseOrderItem).filter_by(purchase_order_id=selected_po_id).all()
                        for item in items:
                            material = session.query(Material).filter_by(id=item.material_id).first()
                            material.quantity -= convert_units(item.quantity, item.unit, material.unit)
                            batch = session.query(MaterialBatch).filter_by(batch_id=item.batch_id).first()
                            if batch:
                                session.delete(batch)
                            session.delete(item)
                        session.delete(db_po)
                        session.commit()
                        refresh_materials()
                        refresh_purchase_orders()
                        refresh_material_batches()
                        st.success("Indkøbsordre og relaterede data slettet med succes!")
                    except Exception as e:
                        session.rollback()
                        st.error(f"Fejl under sletning af indkøbsordre: {str(e)}")
                else:
                    st.warning("Marker 'Bekræft sletning' for at slette indkøbsordren.")

                # The copying functionality was previously under a button in old code
                # You can re-add if needed here

elif action == "Opret et nyt materiale":
    st.header("Opret et nyt materiale")
    material_name = st.text_input("Materialets navn")
    producer_name = st.text_input("Producentnavn")
    unit = st.selectbox("Enhed", ["kg", "g", "l", "ml", "stk"], key="material_unit")
    if st.button("Tilføj materiale"):
        if material_name and unit:
            new_material = Material(name=material_name, unit=unit, producer_name=producer_name)
            try:
                session.add(new_material)
                session.commit()
                refresh_materials()
                st.success("Materiale tilføjet med succes!")
            except Exception as e:
                session.rollback()
                st.error(f"Der opstod en fejl under tilføjelse: {str(e)}")
        else:
            st.error("Udfyld venligst alle felter.")

elif action == "Køb noget":
    st.header("Indkøb til lager")
    if 'purchase_order_items' not in st.session_state:
        st.session_state.purchase_order_items = []
    suppliers = st.session_state.suppliers
    if suppliers:
        supplier = st.selectbox("Vælg leverandør", [(s.id, s.name) for s in suppliers], key="buy_supplier")
        supplier_id, supplier_name = supplier
        st.subheader("Tilføj materialer til indkøbsordren")
        materials = st.session_state.materials
        if materials:
            with st.form("add_purchase_item_form"):
                material = st.selectbox("Vælg materiale", [(m.id, m.name) for m in materials], key="buy_material")
                material_id, material_name = material
                batch_id = st.text_input("Batch ID", key="buy_batch_id")
                quantity = st.number_input("Indkøbt mængde", min_value=0.0, step=0.1, key="buy_quantity")
                unit = st.selectbox("Enhed", ["kg", "g", "l", "ml", "stk"], key="buy_unit")
                add_item_button = st.form_submit_button("Tilføj til indkøbsordre")
            if add_item_button:
                if batch_id.strip() == "":
                    st.error("Batch ID er påkrævet.")
                elif quantity <= 0:
                    st.error("Mængden skal være større end 0.")
                else:
                    st.session_state.purchase_order_items.append({
                        'material_id': material_id,
                        'material_name': material_name,
                        'batch_id': batch_id,
                        'quantity': quantity,
                        'unit': unit
                    })
                    st.success(f"Materiale '{material_name}' tilføjet til indkøbsordren.")

            if st.session_state.purchase_order_items:
                st.subheader("Materialer i indkøbsordren")
                po_items_df = pd.DataFrame(st.session_state.purchase_order_items)
                st.dataframe(po_items_df[['material_name', 'batch_id', 'quantity', 'unit']])
                checked = st.checkbox("Vare modtaget og tjekket")
                date = st.date_input("Dato for indkøb", datetime.now(), key="buy_date")
                invoice_file = st.file_uploader("Upload faktura (PDF eller billede)", type=["pdf", "png", "jpg", "jpeg"], key="invoice_file")
                if st.button("Afgiv indkøbsordre"):
                    try:
                        invoice_file_data = None
                        invoice_filename = None
                        invoice_mimetype = None
                        if invoice_file is not None:
                            invoice_file_data = invoice_file.read()
                            invoice_filename = invoice_file.name
                            invoice_mimetype = invoice_file.type
                        new_purchase_order = PurchaseOrder(
                            supplier_id=supplier_id,
                            date=date,
                            checked=checked,
                            invoice_file=invoice_file_data,
                            invoice_filename=invoice_filename,
                            invoice_mimetype=invoice_mimetype
                        )
                        session.add(new_purchase_order)
                        session.flush()
                        for item in st.session_state.purchase_order_items:
                            new_item = PurchaseOrderItem(
                                purchase_order_id=new_purchase_order.id,
                                material_id=item['material_id'],
                                batch_id=item['batch_id'],
                                quantity=item['quantity'],
                                unit=item['unit']
                            )
                            session.add(new_item)
                            material = session.query(Material).filter_by(id=item['material_id']).first()
                            converted_quantity = convert_units(item['quantity'], item['unit'], material.unit)
                            material.quantity += converted_quantity
                            new_batch = MaterialBatch(
                                material_id=item['material_id'],
                                batch_id=item['batch_id'],
                                quantity=item['quantity'],
                                unit=item['unit'],
                                date=date,
                                checked=checked
                            )
                            session.add(new_batch)
                        session.commit()
                        refresh_materials()
                        refresh_purchase_orders()
                        refresh_material_batches()
                        st.success("Indkøbsordre oprettet og lager opdateret med succes!")
                        st.session_state.purchase_order_items = []
                    except Exception as e:
                        session.rollback()
                        st.error(f"Der opstod en fejl under oprettelse af indkøbsordren: {str(e)}")
            else:
                st.info("Tilføj materialer til indkøbsordren.")
        else:
            st.error("Ingen materialer tilgængelige for køb.")
    else:
        st.error("Ingen leverandører tilgængelige.")

elif action == "Producer noget":
    st.header("Produktionsstyring")
    products = st.session_state.products
    if products:
        product = st.selectbox(
            "Vælg produkt til produktion",
            [(p.id, p.name, p.quantity, p.unit) for p in products],
            format_func=lambda x: f"{x[1]} (Tilgængelig: {x[2]} {x[3]})",
            key="produce_product"
        )
        product_id, product_name, product_quantity, product_unit = product
        recipe = session.query(Recipe).filter_by(product_id=product_id).first()
        if not recipe:
            st.error("Ingen opskrift fundet for det valgte produkt.")
        else:
            bom_items = session.query(BoM).filter_by(recipe_id=recipe.id).all()
            quantity = st.number_input(
                f"Mængde der skal produceres (Standard opskrift producerer {recipe.output_quantity} {product_unit})",
                min_value=0.0,
                step=0.1,
                key="produce_quantity"
            )
            batch_id = st.text_input("Batch ID for det producerede produkt", key="produce_batch_id")
            date = st.date_input("Produktionsdato", datetime.now(), key="produce_date")
            if not bom_items:
                st.error("Ingen stykliste fundet for det valgte produkt.")
            else:
                st.subheader("Vælg batches for hver komponent")
                scaling_factor = quantity / recipe.output_quantity if recipe.output_quantity != 0 else 1
                component_allocations = {}
                materials_map = {m.id: m for m in st.session_state.materials}
                products_map = {p.id: p for p in st.session_state.products}

                for bom in bom_items:
                    required_total = bom.quantity_required * scaling_factor
                    if bom.component_material_id:
                        component = materials_map[bom.component_material_id]
                        available_batches = [b for b in st.session_state.material_batches if b.material_id == component.id and b.quantity > 0]
                    else:
                        component = products_map[bom.component_product_id]
                        available_batches = [b for b in st.session_state.product_batches if b.product_id == component.id and b.quantity > 0]

                    st.write(f"**Komponent: {component.name}**")
                    st.write(f"Krævet mængde: {required_total} {bom.unit}")

                    if available_batches:
                        batch_options = []
                        for b in available_batches:
                            converted_available = convert_units(b.quantity, b.unit, bom.unit)
                            batch_options.append((b.id, f"Batch {b.batch_id} - Tilgængelig: {converted_available} {bom.unit}"))

                        selected_batch_id = st.selectbox(
                            f"Vælg batch for {component.name}",
                            batch_options,
                            format_func=lambda x: x[1],
                            key=f"select_batch_{bom.id}"
                        )
                        chosen_batch_db_id = selected_batch_id[0]
                        chosen_batch = None
                        for b in available_batches:
                            if b.id == chosen_batch_db_id:
                                chosen_batch = b
                                break

                        if chosen_batch:
                            available_converted = convert_units(chosen_batch.quantity, chosen_batch.unit, bom.unit)
                            allocated_quantity = st.number_input(
                                f"Angiv mængde fra valgte batch (max {available_converted} {bom.unit})",
                                min_value=0.0,
                                max_value=available_converted,
                                step=0.1,
                                key=f"allocate_quantity_{bom.id}"
                            )
                            component_allocations[bom.id] = {
                                'component_material_id': bom.component_material_id,
                                'component_product_id': bom.component_product_id,
                                'batch_id': chosen_batch.id,
                                'allocated_quantity': allocated_quantity,
                                'required_total': required_total,
                                'bom_unit': bom.unit
                            }
                        else:
                            component_allocations[bom.id] = None
                    else:
                        st.error("Ingen batches tilgængelige for denne komponent.")
                        component_allocations[bom.id] = None

                if st.button("Opret produktionsordre", key="create_production"):
                    if batch_id.strip() == "":
                        st.error("Batch ID er påkrævet.")
                    else:
                        sufficient_inventory = True
                        for bom_id, alloc in component_allocations.items():
                            if alloc is None or alloc['allocated_quantity'] < alloc['required_total']:
                                sufficient_inventory = False
                                break

                        if not sufficient_inventory:
                            st.error("Der er ikke nok komponenter tildelt til at producere den ønskede mængde.")
                        else:
                            try:
                                new_order = ProductionOrder(product_id=product_id, quantity=quantity, status='Afsluttet', batch_id=batch_id, date=date)
                                session.add(new_order)
                                session.flush()
                                for bom_id, alloc in component_allocations.items():
                                    if alloc['component_material_id']:
                                        batch = session.query(MaterialBatch).filter_by(id=alloc['batch_id']).first()
                                        batch_quantity_to_deduct = convert_units(alloc['allocated_quantity'], alloc['bom_unit'], batch.unit)
                                        batch.quantity -= batch_quantity_to_deduct
                                        material = session.query(Material).filter_by(id=alloc['component_material_id']).first()
                                        material.quantity -= batch_quantity_to_deduct
                                        production_component = ProductionOrderComponent(
                                            production_order_id=new_order.id,
                                            component_material_id=alloc['component_material_id'],
                                            batch_id=batch.id,
                                            quantity_used=alloc['allocated_quantity'],
                                            unit=alloc['bom_unit']
                                        )
                                        session.add(production_component)
                                    else:
                                        batch = session.query(ProductBatch).filter_by(id=alloc['batch_id']).first()
                                        batch_quantity_to_deduct = convert_units(alloc['allocated_quantity'], alloc['bom_unit'], batch.unit)
                                        batch.quantity -= batch_quantity_to_deduct
                                        product_comp = session.query(Product).filter_by(id=alloc['component_product_id']).first()
                                        product_comp.quantity -= batch_quantity_to_deduct
                                        production_component = ProductionOrderComponent(
                                            production_order_id=new_order.id,
                                            component_product_id=alloc['component_product_id'],
                                            batch_id=batch.id,
                                            quantity_used=alloc['allocated_quantity'],
                                            unit=alloc['bom_unit']
                                        )
                                        session.add(production_component)

                                product_to_update = session.query(Product).filter_by(id=product_id).first()
                                product_to_update.quantity += quantity
                                new_product_batch = ProductBatch(
                                    product_id=product_id,
                                    batch_id=batch_id,
                                    quantity=quantity,
                                    unit=product_unit,
                                    date=date
                                )
                                session.add(new_product_batch)
                                session.commit()
                                refresh_materials()
                                refresh_products()
                                refresh_product_batches()
                                refresh_production_orders()
                                st.success("Produktion og batch oprettet med succes!")
                            except Exception as e:
                                session.rollback()
                                st.error(f"Der opstod en fejl under afslutning af produktion: {str(e)}")
    else:
        st.error("Ingen produkter tilgængelige for produktion.")

elif action == "Opret en ny opskrift / stykliste":
    st.header("Opret stykliste (BoM)")
    if "bom_components" not in st.session_state:
        st.session_state.bom_components = []
    st.subheader("1. Opret nyt produkt")
    with st.form("product_creation_form"):
        product_name = st.text_input("Produktnavn", key="bom_product_name")
        unit = st.selectbox("Produkt enhed", ["kg", "g", "l", "ml", "stk"], key="bom_product_unit")
        create_product_button = st.form_submit_button("Opret produkt")
    if create_product_button:
        if product_name and unit:
            new_product = Product(name=product_name, unit=unit)
            try:
                session.add(new_product)
                session.commit()
                refresh_products()
                st.success(f"Produkt '{product_name}' oprettet med succes!")
                st.session_state['product_id'] = new_product.id
            except Exception as e:
                session.rollback()
                st.error(f"Der opstod en fejl under oprettelse af produktet: {str(e)}")
        else:
            st.error("Udfyld venligst alle felter.")

    if 'product_id' in st.session_state:
        product_id = st.session_state['product_id']
        with st.form("recipe_form"):
            method = st.text_area("Fremgangsmåde", key="recipe_method")
            output_quantity = st.number_input("Mængde produceret af opskriften", min_value=0.0, step=0.1, key="recipe_output_quantity")
            save_recipe = st.form_submit_button("Gem opskrift")
        if save_recipe:
            if method and output_quantity > 0:
                new_recipe = Recipe(
                    product_id=product_id,
                    method=method,
                    output_quantity=output_quantity
                )
                try:
                    session.add(new_recipe)
                    session.commit()
                    st.success("Opskrift gemt med succes!")
                    st.session_state['recipe_id'] = new_recipe.id
                except Exception as e:
                    session.rollback()
                    st.error(f"Der opstod en fejl under oprettelse af opskriften: {str(e)}")
            else:
                st.error("Udfyld venligst både fremgangsmåde og mængde.")

    if 'recipe_id' in st.session_state:
        recipe_id = st.session_state['recipe_id']
        st.subheader("3. Tilføj komponenter til stykliste")
        component_type = st.radio("Vælg komponenttype", options=["Materiale", "Produkt"], key="component_type")
        if component_type == "Materiale":
            items = st.session_state.materials
            item_options = [(m.id, m.name) for m in items]
        else:
            items = [p for p in st.session_state.products if p.id != st.session_state['product_id']]
            item_options = [(p.id, p.name) for p in items]

        if items:
            with st.form("add_component_form"):
                component_item = st.selectbox(f"Vælg {component_type.lower()}", item_options, key="component_item")
                quantity_required = st.number_input("Krævet mængde", min_value=0.0, step=0.1, key="quantity_required")
                unit = st.selectbox("Enhed", ["kg", "g", "l", "ml", "stk"], key="component_unit")
                add_component_button = st.form_submit_button("Tilføj komponent")
            if add_component_button:
                item_id, item_name = component_item
                if quantity_required == 0:
                    st.error("Mængden skal være større end 0.")
                else:
                    component_exists = False
                    for component in st.session_state.bom_components:
                        if component_type == component["component_type"] and component["item_id"] == item_id:
                            component["quantity_required"] = quantity_required
                            component["unit"] = unit
                            st.success(f"Komponent '{item_name}' opdateret med succes!")
                            component_exists = True
                            break
                    if not component_exists:
                        st.session_state.bom_components.append({
                            "component_type": component_type,
                            "item_id": item_id,
                            "item_name": item_name,
                            "quantity_required": quantity_required,
                            "unit": unit
                        })
                        st.success(f"Komponent '{item_name}' tilføjet til stykliste med succes!")
        else:
            st.error(f"Ingen {component_type.lower()}er tilgængelige for tilføjelse til stykliste.")

        if st.session_state.bom_components:
            st.subheader("Komponenter tilføjet:")
            components_df = pd.DataFrame(st.session_state.bom_components)
            st.dataframe(components_df[['component_type', 'item_name', 'quantity_required', 'unit']])

        if st.button("Afslut stykliste", key="finalize_bom"):
            try:
                for component in st.session_state.bom_components:
                    if component["component_type"] == "Materiale":
                        new_bom = BoM(
                            recipe_id=recipe_id,
                            component_material_id=component["item_id"],
                            quantity_required=component["quantity_required"],
                            unit=component["unit"]
                        )
                    else:
                        new_bom = BoM(
                            recipe_id=recipe_id,
                            component_product_id=component["item_id"],
                            quantity_required=component["quantity_required"],
                            unit=component["unit"]
                        )
                    session.add(new_bom)
                session.commit()
                refresh_boms()
                st.session_state.bom_components = []
                del st.session_state['product_id']
                del st.session_state['recipe_id']
                st.success("Oprettelse af stykliste afsluttet med succes!")
            except Exception as e:
                session.rollback()
                st.error(f"Der opstod en fejl under tilføjelse af stykliste: {str(e)}")

elif action == "Sælg noget":
    st.header("Salgsstyring")
    products = st.session_state.products
    if products:
        product = st.selectbox(
            "Vælg produkt til salg",
            [(p.id, p.name, p.quantity, p.unit) for p in products],
            format_func=lambda x: f"{x[1]} (Tilgængelig: {x[2]} {x[3]})",
            key="sale_product"
        )
        product_id, product_name, product_quantity, product_unit = product
        customers = st.session_state.customers
        if customers:
            customer = st.selectbox("Vælg kunde", [(c.id, c.name) for c in customers], key="sales_customer")
            customer_id, customer_name = customer
            unit = st.selectbox("Vælg enhed for salg", ["kg", "g", "l", "ml", "stk"], key="sale_unit")
            quantity = st.number_input("Mængde solgt", min_value=0.0, step=0.1, key="sale_quantity")
            date = st.date_input("Salgsdato", datetime.now(), key="sale_date")
            if st.button("Opret salgsordre", key="create_sales_order"):
                converted_quantity = convert_units(quantity, unit, product_unit)
                product_to_update = session.query(Product).filter_by(id=product_id).first()
                if product_to_update and product_to_update.quantity >= converted_quantity:
                    product_to_update.quantity -= converted_quantity
                    new_sales_order = SalesOrder(
                        product_id=product_id,
                        customer_id=customer_id,
                        quantity=quantity,
                        status='Afsluttet',
                        date=date
                    )
                    session.add(new_sales_order)
                    try:
                        session.commit()
                        refresh_products()
                        refresh_sales_orders()
                        st.success("Salgsordre oprettet med succes!")
                    except Exception as e:
                        session.rollback()
                        st.error(f"Der opstod en fejl under oprettelse af salgsordren: {str(e)}")
                else:
                    st.error("Ikke nok lager til at opfylde ordren.")
        else:
            st.error("Ingen kunder tilgængelige. Tilføj venligst en kunde først.")
    else:
        st.error("Ingen produkter tilgængelige for salg.")

elif action == "Flyt noget":
    st.header("Lagerbevægelse")
    st.info("Funktionen er under udvikling.")

elif action == "Smid noget ud":
    st.header("Bortskaffelse af lager")
    disposal_type = st.radio("Vælg type af vare at bortskaffe", options=["Materiale", "Produkt"], key="disposal_type")
    if disposal_type == "Materiale":
        materials = st.session_state.materials
        if materials:
            material = st.selectbox("Vælg materiale", [(m.id, m.name) for m in materials], key="dispose_material")
            material_id, material_name = material
            batches = [b for b in st.session_state.material_batches if b.material_id == material_id and b.quantity > 0]
            if batches:
                batch = st.selectbox(
                    "Vælg batch at bortskaffe fra",
                    [(b.id, b.batch_id, b.quantity, b.unit) for b in batches],
                    format_func=lambda x: f"Batch {x[1]} - Tilgængelig: {x[2]} {x[3]}",
                    key="dispose_material_batch"
                )
                batch_id, batch_name, batch_quantity, batch_unit = batch
                quantity = st.number_input("Mængde at bortskaffe", min_value=0.0, max_value=batch_quantity, step=0.1, key="dispose_quantity")
                reason = st.text_area("Angiv årsag til bortskaffelse", key="dispose_reason")
                date = st.date_input("Dato for bortskaffelse", datetime.now(), key="dispose_date")
                if st.button("Bortskaffel", key="dispose_submit"):
                    if quantity <= 0:
                        st.error("Mængden skal være større end 0.")
                    elif reason.strip() == "":
                        st.error("Årsag er påkrævet.")
                    else:
                        try:
                            batch_to_update = session.query(MaterialBatch).filter_by(id=batch_id).first()
                            batch_to_update.quantity -= quantity
                            material_to_update = session.query(Material).filter_by(id=material_id).first()
                            material_to_update.quantity -= convert_units(quantity, batch_unit, material_to_update.unit)
                            disposal_record = DisposalRecord(
                                material_id=material_id,
                                batch_id=batch_id,
                                quantity=quantity,
                                unit=batch_unit,
                                reason=reason,
                                date=date
                            )
                            session.add(disposal_record)
                            session.commit()
                            refresh_materials()
                            refresh_material_batches()
                            st.success("Bortskaffelse registreret med succes!")
                        except Exception as e:
                            session.rollback()
                            st.error(f"Der opstod en fejl under bortskaffelsen: {str(e)}")
            else:
                st.error("Ingen batches tilgængelige for dette materiale.")
        else:
            st.error("Ingen materialer tilgængelige.")
    else:
        products = st.session_state.products
        if products:
            product = st.selectbox("Vælg produkt", [(p.id, p.name) for p in products], key="dispose_product")
            product_id, product_name = product
            batches = [b for b in st.session_state.product_batches if b.product_id == product_id and b.quantity > 0]
            if batches:
                batch = st.selectbox(
                    "Vælg batch at bortskaffe fra",
                    [(b.id, b.batch_id, b.quantity, b.unit) for b in batches],
                    format_func=lambda x: f"Batch {x[1]} - Tilgængelig: {x[2]} {x[3]}",
                    key="dispose_product_batch"
                )
                batch_id, batch_name, batch_quantity, batch_unit = batch
                quantity = st.number_input("Mængde at bortskaffe", min_value=0.0, max_value=batch_quantity, step=0.1, key="dispose_quantity")
                reason = st.text_area("Angiv årsag til bortskaffelse", key="dispose_reason")
                date = st.date_input("Dato for bortskaffelse", datetime.now(), key="dispose_date")
                if st.button("Bortskaffel", key="dispose_submit"):
                    if quantity <= 0:
                        st.error("Mængden skal være større end 0.")
                    elif reason.strip() == "":
                        st.error("Årsag er påkrævet.")
                    else:
                        try:
                            batch_to_update = session.query(ProductBatch).filter_by(id=batch_id).first()
                            batch_to_update.quantity -= quantity
                            product_to_update = session.query(Product).filter_by(id=product_id).first()
                            product_to_update.quantity -= convert_units(quantity, batch_unit, product_to_update.unit)
                            disposal_record = DisposalRecord(
                                product_id=product_id,
                                batch_id=batch_id,
                                quantity=quantity,
                                unit=batch_unit,
                                reason=reason,
                                date=date
                            )
                            session.add(disposal_record)
                            session.commit()
                            refresh_products()
                            refresh_product_batches()
                            st.success("Bortskaffelse registreret med succes!")
                        except Exception as e:
                            session.rollback()
                            st.error(f"Der opstod en fejl under bortskaffelsen: {str(e)}")
            else:
                st.error("Ingen batches tilgængelige for dette produkt.")
        else:
            st.error("Ingen produkter tilgængelige.")

elif action == "Opret en ny kunde":
    st.header("Opret en ny kunde")
    customer_name = st.text_input("Kundens navn")
    customer_address = st.text_input("Kundens adresse")
    contact_email = st.text_input("Kontakt email")
    phone_number = st.text_input("Telefonnummer")
    vat_number = st.text_input("CVR-nummer")
    if st.button("Tilføj kunde"):
        if all([customer_name, customer_address, contact_email, phone_number, vat_number]):
            new_customer = Customer(
                name=customer_name,
                address=customer_address,
                contact_email=contact_email,
                phone_number=phone_number,
                vat_number=vat_number
            )
            try:
                session.add(new_customer)
                session.commit()
                refresh_customers()
                st.success("Kunde tilføjet med succes!")
            except Exception as e:
                session.rollback()
                st.error(f"Der opstod en fejl under tilføjelse: {str(e)}")
        else:
            st.error("Udfyld venligst alle felter.")

elif action == "Opret en ny leverandør":
    st.header("Opret en ny leverandør")
    supplier_name = st.text_input("Leverandørens navn")
    supplier_address = st.text_input("Leverandørens adresse")
    contact_email = st.text_input("Kontakt email")
    phone_number = st.text_input("Telefonnummer")
    vat_number = st.text_input("CVR-nummer")
    organic_number = st.text_input("Økologinummer")
    report_file = st.file_uploader("Upload leverandørrapport (PDF eller billede)", type=["pdf", "png", "jpg", "jpeg"], key="supplier_report")
    if st.button("Tilføj leverandør"):
        if all([supplier_name, supplier_address, contact_email, phone_number, vat_number]):
            report_file_data = None
            report_filename = None
            report_mimetype = None
            if report_file is not None:
                report_file_data = report_file.read()
                report_filename = report_file.name
                report_mimetype = report_file.type
            new_supplier = Supplier(
                name=supplier_name,
                address=supplier_address,
                contact_email=contact_email,
                phone_number=phone_number,
                vat_number=vat_number,
                organic_number=organic_number,
                report_file=report_file_data,
                report_filename=report_filename,
                report_mimetype=report_mimetype
            )
            try:
                session.add(new_supplier)
                session.commit()
                refresh_suppliers()
                st.success("Leverandør tilføjet med succes!")
            except Exception as e:
                session.rollback()
                st.error(f"Der opstod en fejl under tilføjelse: {str(e)}")
        else:
            st.error("Udfyld venligst alle felter.")
