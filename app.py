import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Date, Boolean, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import pandas as pd
from datetime import datetime

# Import streamlit-option-menu
from streamlit_option_menu import option_menu

# Database setup
Base = declarative_base()

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Database credentials from environment variables
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT', '3306')  # Default MySQL port is 3306
db_name = os.getenv('DB_NAME')

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
    producer_name = Column(String(80), nullable=True)  # New field for producer name
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
    organic_number = Column(String(80), nullable=True)  # New field for organic number


class Recipe(Base):
    __tablename__ = 'recipe'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('product.id'), nullable=False)
    method = Column(Text, nullable=True)  # Use Text for longer text fields
    output_quantity = Column(Float, nullable=False)

class BoM(Base):
    __tablename__ = 'bom'
    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey('recipe.id'), nullable=False)  # Link to recipe
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
    batch_id = Column(Integer, nullable=False)  # Reference to MaterialBatch.id or ProductBatch.id
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

# New table for Material Batches
class MaterialBatch(Base):
    __tablename__ = 'material_batch'
    id = Column(Integer, primary_key=True)
    material_id = Column(Integer, ForeignKey('material.id'), nullable=False)
    batch_id = Column(String(80), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    date = Column(Date, nullable=False)
    checked = Column(Boolean, default=False, nullable=False)

# New table for Product Batches
class ProductBatch(Base):
    __tablename__ = 'product_batch'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('product.id'), nullable=False)
    batch_id = Column(String(80), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    date = Column(Date, nullable=False)

# Table for removed inventory
class DisposalRecord(Base):
    __tablename__ = 'disposal_record'
    id = Column(Integer, primary_key=True)
    material_id = Column(Integer, ForeignKey('material.id'), nullable=True)
    product_id = Column(Integer, ForeignKey('product.id'), nullable=True)
    batch_id = Column(Integer, nullable=False)  # Reference to MaterialBatch.id or ProductBatch.id
    quantity = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    reason = Column(String(255), nullable=False)
    date = Column(Date, nullable=False)

# New tables for Purchase Orders
class PurchaseOrder(Base):
    __tablename__ = 'purchase_order'
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey('supplier.id'), nullable=False)
    date = Column(Date, nullable=False)
    checked = Column(Boolean, default=False, nullable=False)
    items = relationship('PurchaseOrderItem', backref='purchase_order')

class PurchaseOrderItem(Base):
    __tablename__ = 'purchase_order_item'
    id = Column(Integer, primary_key=True)
    purchase_order_id = Column(Integer, ForeignKey('purchase_order.id'), nullable=False)
    material_id = Column(Integer, ForeignKey('material.id'), nullable=False)
    batch_id = Column(String(80), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)

# Set up the database
engine = create_engine(
    f'mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}',
    connect_args={
        'ssl': {
            'ssl_ca': 'C:/Users/avict/OneDrive/Skrivebord/DigiCertGlobalRootCA.crt.pem'
        }
    }
)
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Streamlit App
st.set_page_config(layout="wide")

# Sidebar menu with icons
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

# Helper function to convert units
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

# Main content area
st.header("ERP System")

# Management Page
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
                    st.success("Materiale opdateret med succes!")
                except Exception as e:
                    session.rollback()
                    st.error(f"Fejl under opdatering af materiale: {str(e)}")
    
            if st.button("Slet materiale"):
                confirm_delete = st.checkbox("Bekræft sletning")
                if confirm_delete:
                    try:
                        # Check for dependencies, e.g., if material is used in any BoMs
                        bom_entries = session.query(BoM).filter_by(component_material_id=selected_material_id).all()
                        if bom_entries:
                            st.error("Kan ikke slette materialet, da det bruges i en stykliste.")
                        else:
                            # Check for dependencies in batches
                            material_batches = session.query(MaterialBatch).filter_by(material_id=selected_material_id).all()
                            if material_batches:
                                st.error("Kan ikke slette materialet, da der er tilknyttede batches.")
                            else:
                                session.delete(selected_material)
                                session.commit()
                                st.success("Materiale slettet med succes!")
                    except Exception as e:
                        session.rollback()
                        st.error(f"Fejl under sletning af materiale: {str(e)}")
                else:
                    st.warning("Marker 'Bekræft sletning' for at slette materialet.")
        else:
            st.info("Indtast et gyldigt materiale ID for at redigere eller slette.")


    # Manage Products
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
                    st.success("Produkt opdateret med succes!")
                except Exception as e:
                    session.rollback()
                    st.error(f"Fejl under opdatering af produkt: {str(e)}")
    
            if st.button("Slet produkt"):
                confirm_delete = st.checkbox("Bekræft sletning")
                if confirm_delete:
                    try:
                        # Check for dependencies, e.g., if product is used in any BoMs or Production Orders
                        bom_entries = session.query(BoM).filter(
                            (BoM.component_product_id == selected_product_id) | (BoM.recipe_id == selected_product_id)
                        ).all()
                        production_orders = session.query(ProductionOrder).filter_by(product_id=selected_product_id).all()
                        if bom_entries or production_orders:
                            st.error("Kan ikke slette produktet, da det bruges i en stykliste eller produktionsordre.")
                        else:
                            # Check for dependencies in batches
                            product_batches = session.query(ProductBatch).filter_by(product_id=selected_product_id).all()
                            if product_batches:
                                st.error("Kan ikke slette produktet, da der er tilknyttede batches.")
                            else:
                                session.delete(selected_product)
                                session.commit()
                                st.success("Produkt slettet med succes!")
                    except Exception as e:
                        session.rollback()
                        st.error(f"Fejl under sletning af produkt: {str(e)}")
                else:
                    st.warning("Marker 'Bekræft sletning' for at slette produktet.")
        else:
            st.info("Indtast et gyldigt produkt ID for at redigere eller slette.")


    # Manage Customers
    elif management_option == "Kunder":
        customers = session.query(Customer).all()
        customer_options = [(c.id, c.name, c.address, c.contact_email, c.phone_number, c.vat_number) for c in customers]
        df = pd.DataFrame(customer_options, columns=["ID", "Navn", "Adresse", "Kontakt Email", "Telefonnummer", "CVR-nummer"])
        st.dataframe(df)

        # Editing and deleting customers can be added here if needed

    # Manage Suppliers
    elif management_option == "Leverandører":
        suppliers = session.query(Supplier).all()
        supplier_options = [(s.id, s.name, s.address, s.contact_email, s.phone_number, s.vat_number, s.organic_number) for s in suppliers]
        df = pd.DataFrame(supplier_options, columns=["ID", "Navn", "Adresse", "Kontakt Email", "Telefonnummer", "CVR-nummer", "Økologinummer"])
        st.dataframe(df)

        # Editing and deleting suppliers can be added here if needed

    # Manage Bill of Materials (BoM)
    elif management_option == "Styklister (BoM)":
        boms = session.query(BoM).all()
        bom_options = []
        for b in boms:
            if b.component_material_id:
                component = session.query(Material).filter_by(id=b.component_material_id).first()
                component_name = component.name if component else "Ukendt"
                component_type = "Materiale"
            elif b.component_product_id:
                component = session.query(Product).filter_by(id=b.component_product_id).first()
                component_name = component.name if component else "Ukendt"
                component_type = "Produkt"
            else:
                component_name = "Ukendt"
                component_type = "Ukendt"
    
            recipe = session.query(Recipe).filter_by(id=b.recipe_id).first()
            product = session.query(Product).filter_by(id=recipe.product_id).first()
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
                        st.success("Styklistepost slettet med succes!")
                    except Exception as e:
                        session.rollback()
                        st.error(f"Fejl under sletning af styklistepost: {str(e)}")
                else:
                    st.warning("Marker 'Bekræft sletning' for at slette styklisteposten.")
        else:
            st.info("Indtast et gyldigt stykliste ID for at slette.")


    # Manage Production Orders
    if management_option == "Produktionsordrer":
        production_orders = session.query(ProductionOrder).all()
        production_data = []
        for po in production_orders:
            product = session.query(Product).filter_by(id=po.product_id).first()
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
            product_options = [(p.id, p.name) for p in session.query(Product).all()]
            selected_product_index = next((index for (index, p) in enumerate(product_options) if p[0] == selected_order.product_id), 0)
            new_product_option = st.selectbox("Vælg nyt produkt", product_options, index=selected_product_index)
            new_product_id = new_product_option[0]

            if st.button("Opdater produktionsordre"):
                try:
                    # Update product quantity
                    old_product = session.query(Product).filter_by(id=selected_order.product_id).first()
                    old_product.quantity -= selected_order.quantity

                    new_product = session.query(Product).filter_by(id=new_product_id).first()
                    new_product.quantity += new_quantity

                    # Update production order
                    selected_order.status = new_status
                    selected_order.quantity = new_quantity
                    selected_order.product_id = new_product_id

                    session.commit()
                    st.success("Produktionsordre opdateret med succes!")

                    # Update components used
                    st.subheader("Opdater komponenter brugt i produktionsordren")
                    components_used = session.query(ProductionOrderComponent).filter_by(production_order_id=selected_production_order_id).all()
                    for component in components_used:
                        if component.component_material_id:
                            component_type = "Materiale"
                            comp = session.query(Material).filter_by(id=component.component_material_id).first()
                        else:
                            component_type = "Produkt"
                            comp = session.query(Product).filter_by(id=component.component_product_id).first()
                        new_quantity_used = st.number_input(f"Ny mængde brugt af {component_type} '{comp.name}'", min_value=0.0, step=0.1, value=component.quantity_used, key=f"comp_{component.id}")
                        if st.button(f"Opdater komponent '{comp.name}'", key=f"update_comp_{component.id}"):
                            # Update quantities
                            if component.component_material_id:
                                # Restore old quantity
                                comp.quantity += component.quantity_used
                                # Deduct new quantity
                                comp.quantity -= new_quantity_used
                            else:
                                # Restore old quantity
                                comp.quantity += component.quantity_used
                                # Deduct new quantity
                                comp.quantity -= new_quantity_used
                            component.quantity_used = new_quantity_used
                            session.commit()
                            st.success(f"Komponent '{comp.name}' opdateret med succes!")

                except Exception as e:
                    session.rollback()
                    st.error(f"Fejl under opdatering af produktionsordre: {str(e)}")

            if st.button("Slet produktionsordre"):
                confirm_delete = st.checkbox("Bekræft sletning")
                if confirm_delete:
                    try:
                        # Restore product quantity
                        product = session.query(Product).filter_by(id=selected_order.product_id).first()
                        product.quantity -= selected_order.quantity

                        # Delete product batch
                        product_batch = session.query(ProductBatch).filter_by(batch_id=selected_order.batch_id).first()
                        if product_batch:
                            session.delete(product_batch)

                        # Restore materials/products used in production
                        components_used = session.query(ProductionOrderComponent).filter_by(production_order_id=selected_production_order_id).all()
                        for component in components_used:
                            if component.component_material_id:
                                # Material
                                material = session.query(Material).filter_by(id=component.component_material_id).first()
                                batch = session.query(MaterialBatch).filter_by(id=component.batch_id).first()
                                # Increase batch quantity
                                batch.quantity += component.quantity_used
                                # Increase total material quantity
                                material.quantity += convert_units(component.quantity_used, component.unit, material.unit)
                            else:
                                # Product
                                product_comp = session.query(Product).filter_by(id=component.component_product_id).first()
                                batch = session.query(ProductBatch).filter_by(id=component.batch_id).first()
                                # Increase batch quantity
                                batch.quantity += component.quantity_used
                                # Increase total product quantity
                                product_comp.quantity += convert_units(component.quantity_used, component.unit, product_comp.unit)

                            # Delete ProductionOrderComponent record
                            session.delete(component)

                        # Delete the production order
                        session.delete(selected_order)

                        session.commit()
                        st.success("Produktionsordre slettet og lager opdateret med succes!")
                    except Exception as e:
                        session.rollback()
                        st.error(f"Fejl under sletning af produktionsordre: {str(e)}")
                else:
                    st.warning("Marker 'Bekræft sletning' for at slette produktionsordren.")
        else:
            st.info("Indtast et gyldigt produktionsordre ID for at redigere eller slette.")


    # Manage Sales Orders
    elif management_option == "Salgsordrer":
        sales_orders = session.query(SalesOrder).all()
        sales_data = []
        for so in sales_orders:
            product = session.query(Product).filter_by(id=so.product_id).first()
            customer = session.query(Customer).filter_by(id=so.customer_id).first()
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
                    st.success("Salgsordre opdateret med succes!")
                except Exception as e:
                    session.rollback()
                    st.error(f"Fejl under opdatering af salgsordre: {str(e)}")
    
            if st.button("Slet salgsordre"):
                confirm_delete = st.checkbox("Bekræft sletning")
                if confirm_delete:
                    try:
                        # Restore product quantity
                        product = session.query(Product).filter_by(id=selected_order.product_id).first()
                        product.quantity += selected_order.quantity
    
                        # Optionally, adjust batch quantities if you track batch-specific sales
    
                        # Delete the sales order
                        session.delete(selected_order)
    
                        session.commit()
                        st.success("Salgsordre slettet og lager opdateret med succes!")
                    except Exception as e:
                        session.rollback()
                        st.error(f"Fejl under sletning af salgsordre: {str(e)}")
                else:
                    st.warning("Marker 'Bekræft sletning' for at slette salgsordren.")
        else:
            st.info("Indtast et gyldigt salgsordre ID for at redigere eller slette.")


    # Manage Material Batches
    elif management_option == "Materiale Batches":
        material_batches = session.query(MaterialBatch).all()
        batch_data = []
        for mb in material_batches:
            material = session.query(Material).filter_by(id=mb.material_id).first()
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

    # Manage Purchase Orders
    elif management_option == "Indkøbsordrer":
        st.header("Indkøbsordrer")
        purchase_orders = session.query(PurchaseOrder).all()
        po_data = []
        for po in purchase_orders:
            supplier = session.query(Supplier).filter_by(id=po.supplier_id).first()
            po_data.append({
                "ID": po.id,
                "Leverandør": supplier.name if supplier else "Ukendt",
                "Dato": po.date.strftime("%Y-%m-%d"),
                "Tjekket": "Ja" if po.checked else "Nej"
            })
        df = pd.DataFrame(po_data)
        st.dataframe(df)

        st.subheader("Vis detaljer for en indkøbsordre")
        selected_po_id = st.number_input("Indtast indkøbsordre ID", min_value=1, step=1, key="selected_po_id")
        selected_po = session.query(PurchaseOrder).filter_by(id=selected_po_id).first()
        if selected_po:
            st.write(f"**Leverandør:** {selected_po.supplier_id}")
            st.write(f"**Dato:** {selected_po.date}")
            st.write(f"**Tjekket:** {'Ja' if selected_po.checked else 'Nej'}")
            st.write("**Indkøbte materialer:**")
            items = session.query(PurchaseOrderItem).filter_by(purchase_order_id=selected_po_id).all()
            item_data = []
            for item in items:
                material = session.query(Material).filter_by(id=item.material_id).first()
                item_data.append({
                    "Materiale": material.name if material else "Ukendt",
                    "Batch ID": item.batch_id,
                    "Mængde": item.quantity,
                    "Enhed": item.unit
                })
            item_df = pd.DataFrame(item_data)
            st.dataframe(item_df)

            st.subheader("Rediger eller slet indkøbsordre")
            new_supplier_id = st.selectbox("Vælg ny leverandør", [(s.id, s.name) for s in session.query(Supplier).all()], index=selected_po.supplier_id - 1)
            new_date = st.date_input("Ny dato", value=selected_po.date)
            new_checked = st.checkbox("Vare modtaget og tjekket", value=selected_po.checked)

            if st.button("Opdater indkøbsordre"):
                try:
                    selected_po.supplier_id = new_supplier_id
                    selected_po.date = new_date
                    selected_po.checked = new_checked
                    session.commit()
                    st.success("Indkøbsordre opdateret med succes!")
                except Exception as e:
                    session.rollback()
                    st.error(f"Fejl under opdatering af indkøbsordre: {str(e)}")

            if st.button("Slet indkøbsordre"):
                confirm_delete = st.checkbox("Bekræft sletning")
                if confirm_delete:
                    try:
                        # Restore material quantities
                        for item in items:
                            material = session.query(Material).filter_by(id=item.material_id).first()
                            material.quantity -= convert_units(item.quantity, item.unit, material.unit)
                            # Delete corresponding batches
                            batch = session.query(MaterialBatch).filter_by(batch_id=item.batch_id).first()
                            if batch:
                                session.delete(batch)
                            session.delete(item)
                        session.delete(selected_po)
                        session.commit()
                        st.success("Indkøbsordre og relaterede data slettet med succes!")
                    except Exception as e:
                        session.rollback()
                        st.error(f"Fejl under sletning af indkøbsordre: {str(e)}")
                else:
                    st.warning("Marker 'Bekræft sletning' for at slette indkøbsordren.")

            if st.button("Kopier indkøbsordre"):
                try:
                    new_po = PurchaseOrder(
                        supplier_id=selected_po.supplier_id,
                        date=datetime.now(),
                        checked=selected_po.checked
                    )
                    session.add(new_po)
                    session.flush()  # To get new_po.id
                    for item in items:
                        new_item = PurchaseOrderItem(
                            purchase_order_id=new_po.id,
                            material_id=item.material_id,
                            batch_id=item.batch_id,
                            quantity=item.quantity,
                            unit=item.unit
                        )
                        session.add(new_item)
                    session.commit()
                    st.success(f"Indkøbsordre kopieret med ID {new_po.id}")
                except Exception as e:
                    session.rollback()
                    st.error(f"Fejl under kopiering af indkøbsordre: {str(e)}")
        else:
            st.info("Indtast et gyldigt indkøbsordre ID for at se detaljer.")

    # Manage Product Batches
    elif management_option == "Produkt Batches":
        product_batches = session.query(ProductBatch).all()
        batch_data = []
        for pb in product_batches:
            product = session.query(Product).filter_by(id=pb.product_id).first()
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
        
# Create a new material
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
                st.success("Materiale tilføjet med succes!")
            except Exception as e:
                session.rollback()
                st.error(f"Der opstod en fejl under tilføjelse: {str(e)}")
        else:
            st.error("Udfyld venligst alle felter.")

# Buy something
elif action == "Køb noget":
    st.header("Indkøb til lager")
    if 'purchase_order_items' not in st.session_state:
        st.session_state.purchase_order_items = []
    suppliers = session.query(Supplier).all()
    if suppliers:
        supplier = st.selectbox("Vælg leverandør", [(s.id, s.name) for s in suppliers], key="buy_supplier")
        supplier_id, supplier_name = supplier

        st.subheader("Tilføj materialer til indkøbsordren")

        materials = session.query(Material).all()
        if materials:
            with st.form(key="add_purchase_item_form"):
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

            # Display current purchase order items
            if st.session_state.purchase_order_items:
                st.subheader("Materialer i indkøbsordren")
                po_items_df = pd.DataFrame(st.session_state.purchase_order_items)
                st.dataframe(po_items_df[['material_name', 'batch_id', 'quantity', 'unit']])

                checked = st.checkbox("Vare modtaget og tjekket")
                date = st.date_input("Dato for indkøb", datetime.now(), key="buy_date")

                if st.button("Afgiv indkøbsordre"):
                    try:
                        # Create PurchaseOrder
                        new_purchase_order = PurchaseOrder(
                            supplier_id=supplier_id,
                            date=date,
                            checked=checked
                        )
                        session.add(new_purchase_order)
                        session.flush()  # to get new_purchase_order.id

                        for item in st.session_state.purchase_order_items:
                            # Create PurchaseOrderItem
                            new_item = PurchaseOrderItem(
                                purchase_order_id=new_purchase_order.id,
                                material_id=item['material_id'],
                                batch_id=item['batch_id'],
                                quantity=item['quantity'],
                                unit=item['unit']
                            )
                            session.add(new_item)

                            # Update Material quantity
                            material = session.query(Material).filter_by(id=item['material_id']).first()
                            converted_quantity = convert_units(item['quantity'], item['unit'], material.unit)
                            material.quantity += converted_quantity

                            # Create MaterialBatch
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

# Produce something
elif action == "Producer noget":
    st.header("Produktionsstyring")

    products = session.query(Product).all()

    if products:
        product = st.selectbox(
            "Vælg produkt til produktion",
            [(p.id, p.name, p.quantity, p.unit) for p in products],
            format_func=lambda x: f"{x[1]} (Tilgængelig: {x[2]} {x[3]})",
            key="produce_product"
        )
        product_id, product_name, product_quantity, product_unit = product

        # Fetch Recipe for the selected product
        recipe = session.query(Recipe).filter_by(product_id=product_id).first()
        if not recipe:
            st.error("Ingen opskrift fundet for det valgte produkt.")
        else:
            # Fetch BoM items for the recipe
            bom_items = session.query(BoM).filter_by(recipe_id=recipe.id).all()

            # Input for production quantity
            quantity = st.number_input(
                f"Mængde der skal produceres (Standard opskrift producerer {recipe.output_quantity} {product_unit})",
                min_value=0.0,
                step=0.1,
                key="produce_quantity"
            )

            # Input for new product batch ID
            batch_id = st.text_input("Batch ID for det producerede produkt", key="produce_batch_id")

            # Input for production date
            date = st.date_input("Produktionsdato", datetime.now(), key="produce_date")

            if not bom_items:
                st.error("Ingen stykliste fundet for det valgte produkt.")
            else:
                st.subheader("Fordel komponenter fra batches")
                sufficient_inventory = True
                component_batches = {}

                # Calculate scaling factor based on output quantity
                scaling_factor = quantity / recipe.output_quantity if recipe.output_quantity != 0 else 1

                # Loop over each BoM item to allocate batches
                for bom in bom_items:
                    required_total = bom.quantity_required * scaling_factor
                    if bom.component_material_id:
                        # Component is a material
                        component = session.query(Material).filter_by(id=bom.component_material_id).first()
                        component_name = component.name
                        batches = session.query(MaterialBatch).filter_by(material_id=component.id).filter(MaterialBatch.quantity > 0).all()
                    else:
                        # Component is a product
                        component = session.query(Product).filter_by(id=bom.component_product_id).first()
                        component_name = component.name
                        batches = session.query(ProductBatch).filter_by(product_id=component.id).filter(ProductBatch.quantity > 0).all()

                    st.write(f"**Komponent: {component_name}**")
                    st.write(f"Samlet krævet mængde: {required_total} {bom.unit}")

                    batch_allocations = {}
                    total_allocated = 0

                    if batches:
                        st.write("Vælg batches og tildel mængder:")
                        for batch in batches:
                            available_quantity = convert_units(batch.quantity, batch.unit, bom.unit)
                            allocation_key = f"allocation_{bom.id}_{batch.id}"
                            allocated_quantity = st.number_input(
                                f"Batch {batch.batch_id} - Tilgængelig: {available_quantity} {bom.unit}",
                                min_value=0.0,
                                max_value=available_quantity,
                                step=0.1,
                                key=allocation_key
                            )
                            total_allocated += allocated_quantity
                            if allocated_quantity > 0:
                                batch_allocations[batch.id] = allocated_quantity

                        if total_allocated < required_total:
                            sufficient_inventory = False
                            st.warning(f"Ikke nok af denne komponent i batchene. Tildelt: {total_allocated} {bom.unit}, Krævet: {required_total} {bom.unit}")
                        component_batches[bom.id] = batch_allocations
                    else:
                        st.error("Ingen batches tilgængelige for denne komponent.")
                        sufficient_inventory = False

                if st.button("Opret produktionsordre", key="create_production"):
                    if batch_id.strip() == "":
                        st.error("Batch ID er påkrævet.")
                    elif not sufficient_inventory:
                        st.error("Der er ikke nok komponenter til at producere den ønskede mængde.")
                    else:
                        try:
                            # Add new production order with batch ID and date
                            new_order = ProductionOrder(product_id=product_id, quantity=quantity, status='Afsluttet', batch_id=batch_id, date=date)
                            session.add(new_order)
                            session.flush()  # To get new_order.id before commit

                            # Deduct allocated quantities from batches and record usage
                            for bom in bom_items:
                                allocations = component_batches.get(bom.id, {})
                                for batch_id_allocated, allocated_quantity in allocations.items():
                                    if bom.component_material_id:
                                        batch = session.query(MaterialBatch).filter_by(id=batch_id_allocated).first()
                                        batch_quantity_to_deduct = convert_units(allocated_quantity, bom.unit, batch.unit)
                                        batch.quantity -= batch_quantity_to_deduct
                                        # Update total material quantity
                                        material = session.query(Material).filter_by(id=bom.component_material_id).first()
                                        material.quantity -= batch_quantity_to_deduct
                                        # Record batch usage
                                        production_component = ProductionOrderComponent(
                                            production_order_id=new_order.id,
                                            component_material_id=bom.component_material_id,
                                            batch_id=batch.id,
                                            quantity_used=allocated_quantity,
                                            unit=bom.unit
                                        )
                                        session.add(production_component)
                                    else:
                                        batch = session.query(ProductBatch).filter_by(id=batch_id_allocated).first()
                                        batch_quantity_to_deduct = convert_units(allocated_quantity, bom.unit, batch.unit)
                                        batch.quantity -= batch_quantity_to_deduct
                                        # Update total product quantity
                                        product_component = session.query(Product).filter_by(id=bom.component_product_id).first()
                                        product_component.quantity -= batch_quantity_to_deduct
                                        # Record batch usage
                                        production_component = ProductionOrderComponent(
                                            production_order_id=new_order.id,
                                            component_product_id=bom.component_product_id,
                                            batch_id=batch.id,
                                            quantity_used=allocated_quantity,
                                            unit=bom.unit
                                        )
                                        session.add(production_component)

                            # Update the produced product inventory
                            product_to_update = session.query(Product).filter_by(id=product_id).first()
                            product_to_update.quantity += quantity

                            # Create a new ProductBatch record
                            new_product_batch = ProductBatch(
                                product_id=product_id,
                                batch_id=batch_id,
                                quantity=quantity,
                                unit=product_unit,
                                date=date
                            )
                            session.add(new_product_batch)

                            session.commit()
                            st.success("Produktion og batch oprettet med succes!")
                        except Exception as e:
                            session.rollback()
                            st.error(f"Der opstod en fejl under afslutning af produktion: {str(e)}")
    else:
        st.error("Ingen produkter tilgængelige for produktion.")

# Create a new recipe / BoM
elif action == "Opret en ny opskrift / stykliste":
    st.header("Opret stykliste (BoM)")

    # Initialize bom_components in session state if not present
    if "bom_components" not in st.session_state:
        st.session_state.bom_components = []

    # Product creation form
    st.subheader("1. Opret nyt produkt")
    with st.form(key="product_creation_form"):
        product_name = st.text_input("Produktnavn", key="bom_product_name")
        unit = st.selectbox("Produkt enhed", ["kg", "g", "l", "ml", "stk"], key="bom_product_unit")
        create_product_button = st.form_submit_button("Opret produkt")

        if create_product_button:
            if product_name and unit:
                new_product = Product(name=product_name, unit=unit)
                try:
                    session.add(new_product)
                    session.commit()
                    st.success(f"Produkt '{product_name}' oprettet med succes!")
                    st.session_state['product_id'] = new_product.id
                except Exception as e:
                    session.rollback()
                    st.error(f"Der opstod en fejl under oprettelse af produktet: {str(e)}")
            else:
                st.error("Udfyld venligst alle felter.")

    # Check if product has been created
    if 'product_id' in st.session_state:
        product_id = st.session_state['product_id']
        st.subheader("2. Angiv opskriftsdetaljer")

        method = st.text_area("Fremgangsmåde", key="recipe_method")
        output_quantity = st.number_input("Mængde produceret af opskriften", min_value=0.0, step=0.1, key="recipe_output_quantity")

        if st.button("Gem opskrift", key="save_recipe"):
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

    # Check if recipe has been created
    if 'recipe_id' in st.session_state:
        recipe_id = st.session_state['recipe_id']
        st.subheader("3. Tilføj komponenter til stykliste")

        # Select component type: Material or Product
        component_type = st.radio("Vælg komponenttype", options=["Materiale", "Produkt"], key="component_type")

        if component_type == "Materiale":
            items = session.query(Material).all()
            item_options = [(m.id, m.name) for m in items]
        else:
            # Exclude the product being created to avoid circular references
            items = session.query(Product).filter(Product.id != product_id).all()
            item_options = [(p.id, p.name) for p in items]

        if items:
            with st.form(key="add_component_form"):
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

        # Display the list of components added so far
        if st.session_state.bom_components:
            st.subheader("Komponenter tilføjet:")
            components_df = pd.DataFrame(st.session_state.bom_components)
            st.dataframe(components_df[['component_type', 'item_name', 'quantity_required', 'unit']])

        # Button to finalize the BoM
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
                st.session_state.bom_components = []
                del st.session_state['product_id']  # Reset product_id after finishing BoM
                del st.session_state['recipe_id']
                st.success("Oprettelse af stykliste afsluttet med succes!")
            except Exception as e:
                session.rollback()
                st.error(f"Der opstod en fejl under tilføjelse af stykliste: {str(e)}")

# Sell something
elif action == "Sælg noget":
    st.header("Salgsstyring")

    products = session.query(Product).all()
    if products:
        product = st.selectbox(
            "Vælg produkt til salg",
            [(p.id, p.name, p.quantity, p.unit) for p in products],
            format_func=lambda x: f"{x[1]} (Tilgængelig: {x[2]} {x[3]})",
            key="sale_product"
        )
        product_id, product_name, product_quantity, product_unit = product

        customers = session.query(Customer).all()
        if customers:
            customer = st.selectbox("Vælg kunde", [(c.id, c.name) for c in customers], key="sales_customer")
            customer_id, customer_name = customer

            unit = st.selectbox("Vælg enhed for salg", ["kg", "g", "l", "ml", "stk"], key="sale_unit")

            quantity = st.number_input(
                f"Mængde solgt ({unit})",
                min_value=0.0,
                step=0.1,
                key="sale_quantity"
            )

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

# Move something
elif action == "Flyt noget":
    st.header("Lagerbevægelse")

    st.info("Funktionen er under udvikling.")

# Throw something out
elif action == "Smid noget ud":
    st.header("Bortskaffelse af lager")

    disposal_type = st.radio("Vælg type af vare at bortskaffe", options=["Materiale", "Produkt"], key="disposal_type")

    if disposal_type == "Materiale":
        materials = session.query(Material).all()
        if materials:
            material = st.selectbox("Vælg materiale", [(m.id, m.name) for m in materials], key="dispose_material")
            material_id, material_name = material

            # Fetch batches of the selected material
            batches = session.query(MaterialBatch).filter_by(material_id=material_id).filter(MaterialBatch.quantity > 0).all()
            if batches:
                batch = st.selectbox("Vælg batch at bortskaffe fra", [(b.id, b.batch_id, b.quantity, b.unit) for b in batches],
                                     format_func=lambda x: f"Batch {x[1]} - Tilgængelig: {x[2]} {x[3]}",
                                     key="dispose_material_batch")
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
                            # Deduct quantity from batch and total material quantity
                            batch_to_update = session.query(MaterialBatch).filter_by(id=batch_id).first()
                            batch_to_update.quantity -= quantity

                            material_to_update = session.query(Material).filter_by(id=material_id).first()
                            material_to_update.quantity -= convert_units(quantity, batch_unit, material_to_update.unit)

                            # Create a disposal record
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
                            st.success("Bortskaffelse registreret med succes!")
                        except Exception as e:
                            session.rollback()
                            st.error(f"Der opstod en fejl under bortskaffelsen: {str(e)}")
            else:
                st.error("Ingen batches tilgængelige for dette materiale.")
        else:
            st.error("Ingen materialer tilgængelige.")
    else:  # Product
        products = session.query(Product).all()
        if products:
            product = st.selectbox("Vælg produkt", [(p.id, p.name) for p in products], key="dispose_product")
            product_id, product_name = product

            # Fetch batches of the selected product
            batches = session.query(ProductBatch).filter_by(product_id=product_id).filter(ProductBatch.quantity > 0).all()
            if batches:
                batch = st.selectbox("Vælg batch at bortskaffe fra", [(b.id, b.batch_id, b.quantity, b.unit) for b in batches],
                                     format_func=lambda x: f"Batch {x[1]} - Tilgængelig: {x[2]} {x[3]}",
                                     key="dispose_product_batch")
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
                            # Deduct quantity from batch and total product quantity
                            batch_to_update = session.query(ProductBatch).filter_by(id=batch_id).first()
                            batch_to_update.quantity -= quantity

                            product_to_update = session.query(Product).filter_by(id=product_id).first()
                            product_to_update.quantity -= convert_units(quantity, batch_unit, product_to_update.unit)

                            # Create a disposal record
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
                            st.success("Bortskaffelse registreret med succes!")
                        except Exception as e:
                            session.rollback()
                            st.error(f"Der opstod en fejl under bortskaffelsen: {str(e)}")
            else:
                st.error("Ingen batches tilgængelige for dette produkt.")
        else:
            st.error("Ingen produkter tilgængelige.")


# Create a new customer
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
                st.success("Kunde tilføjet med succes!")
            except Exception as e:
                session.rollback()
                st.error(f"Der opstod en fejl under tilføjelse: {str(e)}")
        else:
            st.error("Udfyld venligst alle felter.")

# Create a new supplier
elif action == "Opret en ny leverandør":
    st.header("Opret en ny leverandør")
    supplier_name = st.text_input("Leverandørens navn")
    supplier_address = st.text_input("Leverandørens adresse")
    contact_email = st.text_input("Kontakt email")
    phone_number = st.text_input("Telefonnummer")
    vat_number = st.text_input("CVR-nummer")
    organic_number = st.text_input("Økologinummer")  # New field for organic number
    if st.button("Tilføj leverandør"):
        if all([supplier_name, supplier_address, contact_email, phone_number, vat_number]):
            new_supplier = Supplier(
                name=supplier_name,
                address=supplier_address,
                contact_email=contact_email,
                phone_number=phone_number,
                vat_number=vat_number,
                organic_number=organic_number
            )
            try:
                session.add(new_supplier)
                session.commit()
                st.success("Leverandør tilføjet med succes!")
            except Exception as e:
                session.rollback()
                st.error(f"Der opstod en fejl under tilføjelse: {str(e)}")
        else:
            st.error("Udfyld venligst alle felter.")
