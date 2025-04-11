import streamlit as st
import pandas as pd
import numpy as np
from src.data_loader import SchemaDetector, COMMON_RELATIONSHIP_TYPES

st.title("Data Analysis")
st.markdown("Analyze the data structure and identify entities and relationships.")

# Initialize session state variables if not already set
if "is_step_available" not in st.session_state:
    st.session_state.is_step_available = lambda step: False  # Default function or logic

# Check if data is available
if 'data' not in st.session_state or st.session_state.data is None:
    st.warning("Please upload data first!")
    if st.button("Go to Data Upload"):
        st.switch_page("pages/1_Data_Upload.py")
else:
    # Infer schema if not already done
    if 'schema' not in st.session_state or st.session_state.schema is None or st.button("Re-analyze Schema"):
        with st.spinner("Analyzing data schema..."):
            st.session_state.schema = SchemaDetector.infer_schema(st.session_state.data)
            st.success("Schema analysis complete!")
    
    # Display schema information
    st.subheader("Column Analysis")
    
    # Create tabs for different schema views
    tab1, tab2, tab3 = st.tabs(["Column Roles", "Data Types", "Relationships"])
    
    with tab1:
        # Group columns by role
        roles = {}
        for col, info in st.session_state.schema["columns"].items():
            role = info["role"]
            if role not in roles:
                roles[role] = []
            roles[role].append(col)
        
        # Display columns by role with ability to change
        for role, columns in roles.items():
            st.write(f"**{role.title()} Columns:**")
            for col in columns:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"- {col} ({st.session_state.schema['columns'][col]['type']})")
                    # Show unique ratio
                    unique_ratio = st.session_state.schema['columns'][col].get('unique_ratio', 0)
                    st.caption(f"Unique values: {unique_ratio:.1%}")
                with col2:
                    new_role = st.selectbox(
                        f"Change {col}",
                        ["identifier", "categorical", "property"],
                        index=["identifier", "categorical", "property"].index(role),
                        key=f"role_{col}"
                    )
                    if new_role != role:
                        st.session_state.schema["columns"][col]["role"] = new_role
                        st.rerun()
    
    with tab2:
        # Group columns by data type
        types = {}
        for col, info in st.session_state.schema["columns"].items():
            col_type = info["type"]
            if col_type not in types:
                types[col_type] = []
            types[col_type].append(col)
        
        # Display columns by type
        for col_type, columns in types.items():
            st.write(f"**{col_type.title()} Columns:**")
            for col in columns:
                st.write(f"- {col} ({st.session_state.schema['columns'][col]['role']})")
                # Show sample values
                if "sample_values" in st.session_state.schema["columns"][col]:
                    samples = st.session_state.schema["columns"][col]["sample_values"]
                    st.write(f"  Sample values: {', '.join(str(x) for x in samples)}")
    
    with tab3:
        # Display detected relationships
        if st.session_state.schema["relationships"]:
            st.write("**Detected Relationships:**")
            for rel in st.session_state.schema["relationships"]:
                col1, col2, col3, col4 = st.columns([3, 3, 2, 1])
                with col1:
                    st.write(f"**{rel['source']}**")
                with col2:
                    st.write(f"**{rel['target']}**")
                with col3:
                    # Allow editing relationship type with dropdown
                    rel_type_options = [rel_type["value"] for rel_type in COMMON_RELATIONSHIP_TYPES] + ["Other (custom)"]
                    
                    if rel['type'] in rel_type_options:
                        index = rel_type_options.index(rel['type'])
                    else:
                        index = rel_type_options.index("Other (custom)")
                    
                    selected_rel_type = st.selectbox(
                        "Type", 
                        rel_type_options,
                        index=index,
                        key=f"type_select_{rel['source']}_{rel['target']}"
                    )
                    
                    if selected_rel_type == "Other (custom)":
                        rel_type = st.text_input(
                            "Custom Type", 
                            value=rel['type'] if rel['type'] not in [r["value"] for r in COMMON_RELATIONSHIP_TYPES] else "",
                            key=f"type_custom_{rel['source']}_{rel['target']}"
                        )
                    else:
                        rel_type = selected_rel_type
                        # Show description
                        for r in COMMON_RELATIONSHIP_TYPES:
                            if r["value"] == selected_rel_type:
                                st.caption(r["description"])
                    
                    if rel_type != rel['type']:
                        rel['type'] = rel_type
                with col4:
                    # Option to remove relationship
                    if st.button("🗑️", key=f"remove_{rel['source']}_{rel['target']}"):
                        st.session_state.schema["relationships"].remove(rel)
                        st.rerun()
        else:
            st.info("No relationships detected automatically")
        
        # Add custom relationship
        st.subheader("Add Custom Relationship")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            source = st.selectbox("Source Column", st.session_state.data.columns)
        with col2:
            target = st.selectbox("Target Column", st.session_state.data.columns)
        with col3:
            # Relationship type dropdown with custom option
            rel_type_options = [rel_type["value"] for rel_type in COMMON_RELATIONSHIP_TYPES] + ["Other (custom)"]
            selected_rel_type = st.selectbox("Relationship Type", rel_type_options, index=0)
            
            if selected_rel_type == "Other (custom)":
                rel_type = st.text_input("Custom Relationship Type")
            else:
                rel_type = selected_rel_type
                # Show description for the selected relationship type
                for r in COMMON_RELATIONSHIP_TYPES:
                    if r["value"] == selected_rel_type:
                        st.caption(r["description"])
        
        if st.button("Add Relationship"):
            new_rel = {
                "source": source,
                "target": target,
                "type": rel_type
            }
            
            # Check if relationship already exists
            exists = False
            for rel in st.session_state.schema["relationships"]:
                if rel["source"] == source and rel["target"] == target:
                    exists = True
                    break
            
            if not exists:
                st.session_state.schema["relationships"].append(new_rel)
                st.success(f"Added relationship: {source} → {target} ({rel_type})")
            else:
                st.warning("This relationship already exists!")
    
    # Entity detection section
    st.subheader("Entity Detection")
    
    # Identify potential entities based on identifier columns
    id_columns = [col for col, info in st.session_state.schema["columns"].items() 
                 if info["role"] == "identifier"]
    
    if id_columns:
        st.write("**Potential Entities:**")
        for id_col in id_columns:
            entity_name = id_col.replace("_id", "").title()
            
            # Find related columns (those that might be properties of this entity)
            related_cols = [col for col in st.session_state.data.columns 
                           if col.startswith(id_col.replace("_id", "")) and col != id_col]
            
            # Display entity info
            st.write(f"- **{entity_name}** (identified by {id_col})")
            if related_cols:
                st.write(f"  Properties: {', '.join(related_cols)}")
            
            # Show sample entity
            if len(st.session_state.data) > 0:
                sample_row = st.session_state.data.iloc[0]
                sample_entity = {col: sample_row[col] for col in [id_col] + related_cols if col in sample_row}
                st.write(f"  Sample: {sample_entity}")
    else:
        st.warning("No identifier columns detected. Consider marking some columns as identifiers.")
    
    # Next step button
    if 'is_step_available' in st.session_state and st.session_state.is_step_available("Graph Builder"):
        st.success("✅ Schema analyzed successfully! You can now proceed to the Graph Builder step.")
        if st.button("Proceed to Graph Builder"):
            st.switch_page("pages/3_Graph_Builder.py")
