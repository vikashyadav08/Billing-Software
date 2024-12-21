from tkinter import *
import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from tkinter import Text
from time import strftime

# Functions for the buttons
def connect_to_db():
    return mysql.connector.connect( host="localhost",user="root", password="@Medha96700!",database="Ducat")
    
def generate_bill():
    try:
        conn = connect_to_db()
        cursor = conn.cursor()

        # Get customer details
        mobile_no = customer_frame.winfo_children()[1].get()
        name = customer_frame.winfo_children()[3].get()
        email = customer_frame.winfo_children()[5].get()

        # Insert customer details
        cursor.execute(
            "INSERT INTO customers (mobile_no, name, email) VALUES (%s, %s, %s)",
            (mobile_no, name, email)
        )
        customer_id = cursor.lastrowid

        # Calculate totals
        cursor.execute("SELECT SUM(price * quantity) AS subtotal FROM cart")
        result = cursor.fetchone()
        sub_total = float(result[0]) if result[0] else 0.0  # Convert Decimal to float

        tax = sub_total * 0.1  # Assuming 10% tax
        total = sub_total + tax

        # Insert bill details
        cursor.execute(
            "INSERT INTO bills (customer_id, sub_total, tax, total) VALUES (%s, %s, %s, %s)",
            (customer_id, sub_total, tax, total)
        )
        bill_id = cursor.lastrowid

        # Display the bill
        bill_text.delete("1.0", "end")
        bill_text.insert("1.0", f"Bill Number: {bill_id}\nCustomer Name: {name}\nMobile No: {mobile_no}\nEmail: {email}\n")
        bill_text.insert("end", "------------------------------------\nProducts:\n")

        cursor.execute(
            "SELECT p.name, c.quantity, c.price "
            "FROM cart c JOIN products p ON c.product_id = p.id"
        )
        for product, quantity, price in cursor.fetchall():
            bill_text.insert("end", f"{product} - Qty: {quantity} - Price: {float(price):.2f}\n")

        bill_text.insert("end", "------------------------------------\n")
        bill_text.insert("end", f"Sub Total: {sub_total:.2f}\nTax: {tax:.2f}\nTotal: {total:.2f}\n")

        cursor.execute("DELETE FROM cart")
        conn.commit()
    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        conn.close()

        
def add_to_cart():
    try:
        conn = connect_to_db()
        cursor = conn.cursor()

        # Fetch selected product details
        selected_product = product_name.get()
        quantity = int(product_entries[4].get())  # Quantity input
        price = float(product_entries[3].get())  # Price input

        # Check for valid inputs
        if not selected_product or quantity <= 0 or price <= 0:
            messagebox.showerror("Input Error", "Please enter valid product details.")
            return

        # Insert into cart
        cursor.execute(
            "INSERT INTO cart (product_id, quantity, price) "
            "VALUES ((SELECT id FROM products WHERE name = %s), %s, %s)",
            (selected_product, quantity, price)
        )
        conn.commit()
        messagebox.showinfo("Success", "Product added to cart.")
    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        conn.close()


def save_bill():
    try:
        # Fetch bill data from bill_text
        bill_data = bill_text.get("1.0", "end").strip()
        
        # Check if bill_text is empty
        if not bill_data or bill_data == "1.0":
            messagebox.showerror("Error", "No bill to save. Please generate a bill first.")
            return

        # Save the bill data to a file
        with open("bill.txt", "w") as f:
            f.write(bill_data)
        messagebox.showinfo("Success", "Bill saved to bill.txt")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def clear_fields():
    customer_frame.winfo_children()[1].delete(0, "end")
    customer_frame.winfo_children()[3].delete(0, "end")
    customer_frame.winfo_children()[5].delete(0, "end")
    for entry in product_entries:
        entry.delete(0, "end")
    bill_text.delete("1.0", "end")

def exit_app():
    top.destroy()


def search_bill():
    try:
        bill_number = bill_number_entry.get()

        if not bill_number.strip():
            messagebox.showerror("Error", "Bill number cannot be empty!")
            return

        conn = connect_to_db()
        cursor = conn.cursor()

        # Fetch bill and customer details
        query = """
            SELECT b.id AS bill_id, c.name AS customer_name, c.mobile_no, c.email, 
                   b.sub_total, b.tax, b.total
            FROM bills b
            JOIN customers c ON b.customer_id = c.id
            WHERE b.id = %s
        """
        cursor.execute(query, (bill_number,))
        bill_data = cursor.fetchone()

        if not bill_data:
            messagebox.showinfo("Not Found", f"No bill found with Bill Number: {bill_number}")
            return

        # Unpack bill data
        bill_id, customer_name, mobile_no, email, sub_total, tax, total = bill_data

        # Display bill header
        bill_text.delete("1.0", "end")
        bill_text.insert("1.0", f"Bill Number: {bill_id}\nCustomer Name: {customer_name}\n")
        bill_text.insert("end", f"Mobile No: {mobile_no}\nEmail: {email}\n")
        bill_text.insert("end", "-" * 36 + "\nProducts:\n")

        # Fetch product details
        product_query = """
            SELECT p.name AS product_name, c.quantity, c.price
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.bill_id = %s
        """
        cursor.execute(product_query, (bill_id,))
        products = cursor.fetchall()

        if products:
            for product_name, quantity, price in products:
                bill_text.insert("end", f"{product_name} - Qty: {quantity} - Price: {price:.2f}\n")
            bill_text.insert("end", "-" * 36 + "\n")
        else:
            bill_text.insert("end", "No products found for this bill.\n")

        # Display totals
        bill_text.insert("end", f"Sub Total: {sub_total:.2f}\nTax: {tax:.2f}\nTotal: {total:.2f}\n")

        conn.commit()
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
    finally:
        conn.close()


        
def calculate_total():
    try:
        # Get the Sub Total value
        subtotal = float(entry_fields[0].get())
        # Calculate tax (18%)
        tax = subtotal * 0.18
        # Calculate total
        total = subtotal + tax
        
        # Update the "Govt Tax" and "Total" fields
        entry_fields[1].delete(0, tk.END)
        entry_fields[1].insert(0, f"{tax:.2f}")
        entry_fields[2].delete(0, tk.END)
        entry_fields[2].insert(0, f"{total:.2f}")
    except ValueError:
        # Handle invalid input
        entry_fields[1].delete(0, tk.END)
        entry_fields[1].insert(0, "Error")
        entry_fields[2].delete(0, tk.END)
        entry_fields[2].insert(0, "Error")

def clear_frame_data():
    try:
        # Clear all customer details (Entries in customer_frame)
        for widget in customer_frame.winfo_children():
            if isinstance(widget, tk.Entry):
                widget.delete(0, tk.END)  # Clear text in Entry widgets
        
    
        for widget in product_frame.winfo_children():
            if isinstance(widget, tk.Entry):
                widget.delete(0, tk.END)  # Clear text in Entry widgets
            elif isinstance(widget, ttk.Combobox):
                widget.set("")  # Reset Combobox selection

        # Clear the Bill Area (Text widget)
        bill_text.delete("1.0", tk.END)

        # Clear Bill Counter section (Sub Total, Govt Tax, Total)
        for widget in counter_frame.winfo_children():
            if isinstance(widget, tk.Entry):
                widget.delete(0, tk.END)  

        # messagebox.showinfo("Success", "All fields in the frames have been cleared.")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")


        
def print_bill():
    try:
        bill_data = bill_text.get("1.0", "end").strip()
        if not bill_data:
            messagebox.showerror("Error", "No bill to print. Please generate a bill first.")
            return

        messagebox.showinfo("Print", "Bill sent to the printer.")
    except Exception as e:
        messagebox.showerror("Error", str(e))




top = tk.Tk()
top.title("Billing Software")
top.geometry("1500x700")

def time():
    string = strftime("%d-%m-%y   %H:%M:%S")  
    time_label.config(text=string)  
    time_label.after(1000, time)  

time_label = Label(top, font=("Arial", 15, "bold"), fg="Dark Orange")
time_label.place(x=0, y=5)  
time()





# Header
L = Label(top, text="BILLING SOFTWARE BY VIKASH", font=("Arial", 24, "bold"), fg="dark orange").pack(pady=10)
 
#customer
customer_frame = tk.LabelFrame(top, text="Customer", font=("Arial", 12, "bold"), fg="orange")
customer_frame.place(x=20, y=100, width=670, height=180)
customer_labels = ["Mobile No:", "Customer Name:", "Email:"]
for i, text in enumerate(customer_labels):
    tk.Label(customer_frame, text=text, font=("Arial", 12, "bold")).grid(row=i, column=0, padx=10, pady=5, sticky="w")
    tk.Entry(customer_frame, font=("Arial", 12, "bold")).grid(row=i, column=1, padx=10, pady=5)
    
# Product Frame
def update_subcategories(event):
    selected_category = categories.get()
    if selected_category == "Clothing":
        sub_category['values'] = ["Pant", "Shirt", "T-shirt", "Lower", "Jacket"]
        product_name['values'] = ["Jeans", "Formal Shirt", "Casual T-shirt", "Track Pants", "Winter Jacket"]
    elif selected_category == "Electronics":
        sub_category['values'] = ["Mobile", "Laptop", "Headphone", "Camera", "Smartwatch"]
        product_name['values'] = ["iPhone", "Dell Laptop", "Sony Headphones", "Canon Camera", "Apple Watch"]
    elif selected_category == "Grocery":
        sub_category['values'] = ["Vegetables", "Fruits", "Snacks", "Beverages", "Dairy"]
        product_name['values'] = ["Tomatoes", "Apples", "Chips", "Juice", "Milk"]
    else:
        sub_category['values'] = []
        product_name['values'] = []

    sub_category.set("")  # Clear current selection
    product_name.set("")  # Clear current selection

# Create the LabelFrame for Product

product_frame = tk.LabelFrame(top, text="Product", font=("Arial", 12, "bold"), fg="orange")
product_frame.place(x=20, y=280, width=670, height=270)
tk.Button(product_frame, text="Add to Cart", font=("Arial", 12, "bold"), bg="orange", command=add_to_cart).grid(row=5, column=0, columnspan=2, pady=10)


# Labels and Inputs
product_labels = ["Select Categories:", "Sub Category:", "Product Name:", "Price:", "Quantity:"]
product_entries = []

for i, text in enumerate(product_labels):
    tk.Label(product_frame, text=text, font=("Arial", 12, "bold")).grid(row=i, column=0, padx=10, pady=5, sticky="w")
    
    if text == "Select Categories:":
        categories = ttk.Combobox(product_frame, font=("Arial", 12, "bold"), values=["Clothing", "Electronics", "Grocery"])
        categories.grid(row=i, column=1, padx=10, pady=5)
        categories.bind("<<ComboboxSelected>>", update_subcategories)  
        product_entries.append(categories)
    elif text == "Sub Category:":
        sub_category = ttk.Combobox(product_frame, font=("Arial", 12, "bold"))
        sub_category.grid(row=i, column=1, padx=10, pady=5)
        product_entries.append(sub_category)
    elif text == "Product Name:":
        product_name = ttk.Combobox(product_frame, font=("Arial", 12, "bold"))
        product_name.grid(row=i, column=1, padx=10, pady=5)
        product_entries.append(product_name)
    else:
        entry = tk.Entry(product_frame, font=("Arial", 12, "bold"))
        entry.grid(row=i, column=1, padx=10, pady=5)
        product_entries.append(entry)
    
 
#Bill        
bill_frame = tk.LabelFrame(top, text="Bill Area", font=("Arial", 12, "bold"), fg="orange")
bill_frame.place(x=700, y=100, width=790, height=450)

bill_text = Text(bill_frame, font=("Arial", 12, "bold"))
bill_text.pack(fill="both", expand=True)


#Search

bill_number_label = Label(top, text="Bill Number:", font=("Arial", 12, "bold"))
bill_number_label.place(x=700, y=70)

bill_number_entry = Entry(top, font=("Arial", 12), width=20)  # Entry widget for Bill Number
bill_number_entry.place(x=950, y=70, width=400)

search_button = Button(top, text="Search", font=("Arial", 12, "bold"), bg="orange", command=search_bill)
search_button.place(x=1360, y=68)

# Billing Counter Frame
counter_frame = tk.LabelFrame(top, text="Bill Counter", font=("Arial", 12, "bold"), fg="orange")
counter_frame.place(x=20, y=550, width=1470, height=140)

# Labels and Entry Fields
counter_labels = ["Sub Total:", "Govt Tax:", "Total:"]
entry_fields = []

for i, text in enumerate(counter_labels):
    tk.Label(counter_frame, text=text, font=("Arial", 12, "bold")).grid(row=0, column=i*2, padx=10, pady=5, sticky="w")
    entry = tk.Entry(counter_frame, font=("Arial", 12, "bold"))
    entry.grid(row=0, column=i*2+1, padx=10, pady=5)
    entry_fields.append(entry)

# Buttons
# Update the "Clear" button command
button_texts = ["Generate Bill", "Save Bill", "Print", "Clear", "Total", "Exit"]
button_commands = [generate_bill, save_bill, print_bill, clear_frame_data, calculate_total, exit_app]
for i, (text, cmd) in enumerate(zip(button_texts, button_commands)):
    tk.Button(counter_frame, text=text, font=("Arial", 12, "bold"), bg="orange", command=cmd).grid(row=1, column=i, padx=85, pady=25)


top.mainloop()