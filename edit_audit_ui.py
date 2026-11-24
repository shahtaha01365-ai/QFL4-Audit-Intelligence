import hashlib
import re
from datetime import date

import pandas as pd
import streamlit as st


def render_edit_defect_entry(load_data, save_data, upload_image, delete_images, find_col, drive_file_id):
    st.title("Edit defect entry")
    st.caption("Choose a vehicle and update one of its saved defect entries.")

    load_data.clear()
    data = load_data()
    chassis_col = find_col(data, ["Chassis No", "Chassis", "Chassis Number"])
    if not chassis_col:
        st.error("The Chassis No. column was not found in the spreadsheet.")
        return

    chassis_values = sorted(
        data[chassis_col].dropna().astype(str).str.strip().loc[lambda values: values.ne("")].unique().tolist()
    )
    if not chassis_values:
        st.info("No audit records are available to edit.")
        return

    chassis = st.selectbox("Select vehicle chassis number", chassis_values, key="edit_defect_chassis")
    row_indexes = data.index[
        data[chassis_col].fillna("").astype(str).str.strip().str.casefold() == chassis.casefold()
    ].tolist()
    if not row_indexes:
        st.info("No matching audit record was found.")
        return
    if len(row_indexes) > 1:
        st.warning(f"Found {len(row_indexes)} records for this chassis. The first matching record will be edited.")
    row_index = row_indexes[0]
    row = data.loc[row_index]

    # Excel loaders may return Arrow-backed string columns. Convert before
    # editing so pandas can safely accept values of a different type (for
    # example, an integer in a quantity column).
    data = data.astype(object)
    row = data.loc[row_index]

    slots = []
    for col in data.columns:
        match = re.fullmatch(r"Defect\s*(\d+)", str(col).strip(), flags=re.IGNORECASE)
        value = row.get(col, "")
        if match and not pd.isna(value) and str(value).strip():
            slots.append((int(match.group(1)), col))
    slots.sort()
    if not slots:
        st.info("This vehicle has no defect entries to edit.")
        return

    chassis_key = hashlib.sha1(chassis.encode("utf-8")).hexdigest()[:10]
    slot = st.selectbox(
        "Select defect entry", [number for number, _ in slots],
        format_func=lambda number: f"Defect entry {number}",
        key=f"edit_defect_slot_{chassis_key}",
    )
    defect_col = find_col(data, [f"Defect {slot}"])

    def cell(name, fallback=""):
        col = find_col(data, [name])
        value = row.get(col, fallback) if col else fallback
        return fallback if pd.isna(value) else str(value).strip()

    parts = [part.strip() for part in str(row.get(defect_col, "")).split("|")]
    parts += [""] * max(0, 5 - len(parts))
    image_col = find_col(data, [f"Defect Image {slot}"])
    old_image = cell(f"Defect Image {slot}") if image_col else ""
    if old_image:
        st.link_button("Open current defect photo", old_image, icon=":material/open_in_new:")

    type_options = ["Safety", "Functional", "Major Aesthetics", "Minor Aesthetics"]
    current_type = cell(f"Defect Type {slot}", cell("Defect Type", "Safety"))
    if current_type not in type_options:
        type_options.append(current_type)
    category_options = [
        "Over Tightening", "Looseness", "Scratch", "Rust", "Improperly installed", "Weld Spot Burr",
        "Weld Spot Miss", "Sag", "Run", "Dent", "Bump", "Spot Miss", "Seepage", "Leakage",
        "Crater", "Thin Paint", "Part Miss", "Harness Routing Wrong", "Wrong Part", "Deformation",
        "Gap NG", "Indicator not work", "Wrinkles", "Torque Mark Miss", "Other",
    ]
    current_category = cell(f"Defect Category {slot}", cell("Defect Category", "Other"))
    if current_category not in category_options:
        category_options.append(current_category)
    department_options = ["Weld Shop", "Paint Shop", "Assembly Shop", "Tester Line", "Final Confirmation", "QA Receiving", "CKD"]
    current_department = cell(f"Department {slot}", cell("Department", "Weld Shop"))
    if current_department not in department_options:
        department_options.append(current_department)
    class_options = ["A", "B", "C", "D"]
    current_class = cell(f"Defect Class {slot}", "A")
    if current_class not in class_options:
        class_options.append(current_class)
    zone_options = ["A", "B", "C", "D"]
    current_zone = cell(f"Zone {slot}", "A")
    if current_zone not in zone_options:
        zone_options.append(current_zone)
    locations = ["RH", "LH", "FR", "RR"]
    areas = ["Side", "Upper Side", "Lower Side"]
    if parts[1] and parts[1] not in areas:
        areas.append(parts[1])

    date_col = find_col(data, ["Date", "Audit Date"])
    raw_date = row.get(date_col) if date_col else None
    parsed_date = pd.to_datetime(raw_date, errors="coerce")
    current_date = parsed_date.date() if pd.notna(parsed_date) else date.today()

    with st.form(f"edit_defect_form_{chassis_key}_{slot}"):
        audit_date = st.date_input("Audit date", value=current_date)
        left, right = st.columns(2)
        with left:
            defect_type = st.selectbox("Defect type", type_options, index=type_options.index(current_type))
            defect_category = st.selectbox("Defect category", category_options, index=category_options.index(current_category))
            department = st.selectbox("Department", department_options, index=department_options.index(current_department))
            quantity_value = pd.to_numeric(cell(f"QTY {slot}", "1"), errors="coerce")
            quantity = st.number_input("Quantity", min_value=1, step=1, value=max(1, int(quantity_value) if pd.notna(quantity_value) else 1))
        with right:
            defect_class = st.selectbox("Defect class", class_options, index=class_options.index(current_class))
            zone = st.selectbox("Zone", zone_options, index=zone_options.index(current_zone))
            vehicle_location = st.selectbox("Vehicle location", locations, index=locations.index(parts[0]) if parts[0] in locations else 0)
            area = st.selectbox("Area", areas, index=areas.index(parts[1]) if parts[1] in areas else 0)
            part_name = st.text_input("Part name", value=parts[2])
            part_location = st.selectbox("Part location", locations, index=locations.index(parts[3]) if parts[3] in locations else 0)
            description = st.text_input("Defect description", value=parts[4])
        replacement_image = st.file_uploader(
            "Replace defect photo (optional)", type=["jpg", "jpeg", "png", "webp"],
            key=f"edit_defect_image_{chassis_key}_{slot}",
        )
        remove_image = st.checkbox("Remove current photo", disabled=not bool(old_image))
        submitted = st.form_submit_button("Save defect changes", type="primary")

    if not submitted:
        return
    if not part_name.strip() or not description.strip():
        st.error("Part name and defect description are required.")
        return

    if date_col is None:
        date_col = "Date"
        data[date_col] = pd.NaT
    data.at[row_index, date_col] = pd.Timestamp(audit_date)

    old_file_id = drive_file_id(old_image)
    new_image = old_image
    if replacement_image is not None:
        new_image = upload_image(replacement_image)
    elif remove_image:
        new_image = ""

    data.at[row_index, defect_col] = " | ".join([
        vehicle_location, area, part_name.strip(), part_location, description.strip()
    ])
    updates = {
        f"Defect Type {slot}": defect_type,
        f"Defect Category {slot}": defect_category,
        f"Department {slot}": department,
        f"Defect Class {slot}": defect_class,
        f"Zone {slot}": zone,
        f"QTY {slot}": int(quantity),
        f"Defect Image {slot}": new_image,
    }
    for name, value in updates.items():
        col = find_col(data, [name])
        if col is None:
            col = name
            data[col] = pd.NA
        data.at[row_index, col] = value
    if slot == 1:
        for name, value in [("Defect Type", defect_type), ("Defect Category", defect_category), ("Department", department)]:
            col = find_col(data, [name])
            if col is None:
                col = name
                data[col] = pd.NA
            data.at[row_index, col] = value

    # Keep the leading CLASS/ZONE summary cells in sync with the numbered
    # defect entries. The dashboard and exported audit sheet use these totals.
    for field, summary_prefix, options in (
        ("Defect Class", "CLASS", "ABCD"),
        ("Zone", "ZONE", "ABCD"),
    ):
        entry_columns = []
        for col in data.columns:
            match = re.fullmatch(rf"{field}\s*(\d+)", str(col).strip(), flags=re.IGNORECASE)
            if match:
                entry_columns.append((int(match.group(1)), col))
        for option in options:
            total = 0
            for number, entry_col in entry_columns:
                qty_col = find_col(data, [f"QTY {number}", f"Quantity {number}"])
                if not qty_col:
                    continue
                raw_entry_value = data.at[row_index, entry_col]
                entry_value = "" if pd.isna(raw_entry_value) else str(raw_entry_value).strip().upper()
                if entry_value == option:
                    qty_value = pd.to_numeric(
                        pd.Series([data.at[row_index, qty_col]]), errors="coerce"
                    ).fillna(0).iloc[0]
                    total += int(qty_value)
            summary_col = find_col(data, [f"{summary_prefix} {option}", f"{summary_prefix}_{option}"])
            if summary_col is None:
                summary_col = f"{summary_prefix} {option}"
                data[summary_col] = 0
            data.at[row_index, summary_col] = total

    total_qty_col = find_col(data, ["QTY"])
    qty_cols = [col for col in data.columns if re.fullmatch(r"QTY\s*\d+", str(col).strip(), flags=re.IGNORECASE)]
    if total_qty_col and qty_cols:
        qty_values = pd.to_numeric(data.loc[row_index, qty_cols], errors="coerce").fillna(0)
        data.at[row_index, total_qty_col] = int(qty_values.sum())

    save_data(data)
    photo_note = ""
    if old_file_id and old_file_id != drive_file_id(new_image):
        try:
            removed, failed = delete_images([old_image])
            photo_note = f" Previous photo removed: {removed}."
            if failed:
                photo_note += f" {failed} previous photo could not be removed."
        except Exception:
            photo_note = " The old photo could not be removed from Drive."
    st.success(f"Defect entry {slot} for chassis {chassis} was updated.{photo_note}")
