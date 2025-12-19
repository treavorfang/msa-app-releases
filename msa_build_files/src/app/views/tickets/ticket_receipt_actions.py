# src/app/views/tickets/ticket_receipt_actions.py
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QCheckBox, QFileDialog
import os
import shutil
from dtos.customer_dto import CustomerDTO
from dtos.ticket_dto import TicketDTO
from utils.validation.message_handler import MessageHandler
from utils.print.ticket_generator import TicketReceiptGenerator
from utils.language_manager import language_manager
import traceback

class TicketReceiptActions:
    def __init__(self, ticket_receipt):
        self.ticket_receipt = ticket_receipt
        self.lm = language_manager
        # Access business_settings_service from the parent ticket_receipt object
        business_settings_service = getattr(ticket_receipt, 'business_settings_service', None)
        self.print_generator = TicketReceiptGenerator(ticket_receipt, business_settings_service)
        self._create_widgets()
    
    def _create_widgets(self):
        """Create action-related widgets"""
        self.submit_btn = QPushButton(self.lm.get("TicketActions.submit_ticket", "Submit Ticket"))
        self.preview_btn = QPushButton(self.lm.get("TicketActions.preview_ticket", "Preview Ticket"))
        self.save_pdf_btn = QPushButton(self.lm.get("TicketActions.save_pdf", "Save PDF"))
        self.print_chk = QCheckBox(self.lm.get("TicketActions.print_ticket", "Print Ticket"))
        
        # Load default state from settings
        try:
             settings_service = self.ticket_receipt.container.settings_service
             user_id = self.ticket_receipt.user_id
             settings = settings_service.get_user_settings(user_id)
             self.print_chk.setChecked(settings.get('auto_print_ticket', True))
        except Exception:
             self.print_chk.setChecked(True)
    
    def create_button_section(self):
        """Create and return the button section"""
        layout = QHBoxLayout()
        layout.addStretch()
        
        self.submit_btn.setDefault(True)
        self.preview_btn.clicked.connect(self.handle_preview)
        self.save_pdf_btn.clicked.connect(self.handle_save_pdf)
        
        layout.addWidget(self.print_chk)
        layout.addWidget(self.preview_btn)
        layout.addWidget(self.save_pdf_btn)
        layout.addWidget(self.submit_btn)
        return layout
    
    def validate_inputs_silent(self) -> bool:
        """Validate all form inputs without showing error messages"""
        validators = [
            self.ticket_receipt.customer_section.validate_silent,
            self.ticket_receipt.device_section.validate_silent,
            self.ticket_receipt.issue_section.validate_silent,
            self.ticket_receipt.controls_section.validate_costs_silent
        ]
        
        return all(validator() for validator in validators)

    def _gather_ticket_data_for_print(self, ticket_dto=None):
        """Gather all current form data for printing"""
        return self.ticket_receipt._gather_ticket_data_for_print(ticket_dto)

    def handle_save_pdf(self):
        """Handle Save PDF button click"""
        print("DEBUG: handle_save_pdf called")
        try:
            if not self.validate_inputs_silent():
                print("DEBUG: Validation failed")
                errors = []
                if not self.ticket_receipt.customer_section.validate_silent(): errors.append("Customer information is incomplete")
                if not self.ticket_receipt.device_section.validate_silent(): errors.append("Device information is incomplete")
                if not self.ticket_receipt.issue_section.validate_silent(): errors.append("Issue details are incomplete")
                if not self.ticket_receipt.controls_section.validate_costs_silent(): errors.append("Cost information is invalid")
                
                error_msg = "\n".join(errors) if errors else "Please fill in all required fields."
                MessageHandler.show_warning(self.ticket_receipt, "Validation Error", error_msg)
                return

            data = self._gather_ticket_data_for_print()
            print(f"DEBUG: Data gathered for ticket: {data.get('ticket_number')}")
            
            # Use safe filename logic
            ticket_number = data.get('ticket_number', 'Ticket')
            safe_filename = f"Ticket-{ticket_number.replace('/', '-').replace('\\', '-')}.pdf"
            desktop_path = os.path.join(os.path.expanduser("~/Desktop"), safe_filename)
            print(f"DEBUG: Suggesting path: {desktop_path}")
            
            # Prompt user for location
            # Use None as parent to avoid potential window modality crashes
            file_path, _ = QFileDialog.getSaveFileName(
                None,
                self.lm.get("TicketActions.save_pdf_dialog", "Save Ticket as PDF"),
                desktop_path,
                "PDF Files (*.pdf)"
            )
            print(f"DEBUG: User selected path: {file_path}")
            
            if file_path:
                print("DEBUG: Calling _print_to_pdf")
                self.print_generator._print_to_pdf(data, file_path)
                print("DEBUG: PDF generation successful")
                MessageHandler.show_info(self.ticket_receipt, "Success", f"Ticket saved to {file_path}")
                
        except Exception as e:
             print(f"ERROR in handle_save_pdf: {e}")
             import traceback
             traceback.print_exc()
             MessageHandler.show_critical(self.ticket_receipt, "Error", f"Failed to save PDF: {str(e)}")

    def handle_preview(self):
        """Handle preview button click"""
        try:
            if not self.validate_inputs_silent():
                # Provide specific error messages
                errors = []
                if not self.ticket_receipt.customer_section.validate_silent():
                    errors.append("Customer information is incomplete or invalid")
                if not self.ticket_receipt.device_section.validate_silent():
                    errors.append("Device information is incomplete or invalid")
                if not self.ticket_receipt.issue_section.validate_silent():
                    errors.append("Issue details are incomplete (select an error type)")
                if not self.ticket_receipt.controls_section.validate_costs_silent():
                    errors.append("Cost information is invalid")
                
                error_msg = "\n".join(errors) if errors else self.lm.get("Tickets.fill_required_before_preview", "Please fill in all required fields before previewing.")
                MessageHandler.show_warning(self.ticket_receipt, self.lm.get("Tickets.validation_error", "Validation Error"), error_msg)
                return
                
            data = self._gather_ticket_data_for_print()
            
            # Get print format preference
            user_settings = self.ticket_receipt.container.settings_service.get_user_settings(self.ticket_receipt.user_id)
            data['print_format'] = user_settings.get('print_format', 'Standard A5')
            
            self.print_generator.preview_ticket(data)
        except Exception as e:
            MessageHandler.show_critical(self.ticket_receipt, self.lm.get("Tickets.preview_error", "Preview Error"), f"{self.lm.get('Tickets.failed_preview', 'Failed to generate preview')}: {str(e)}")
    
    def create_new_ticket(self):
        """Create a new ticket after validating all inputs"""
        try:
            customer_data = self.ticket_receipt.customer_section.get_customer_data()
            
            if 'customer_id' in customer_data:
                customer_id = customer_data['customer_id']
            else:
                # Create new customer
                customer_dto = CustomerDTO(
                    name=customer_data['name'],
                    phone=customer_data['phone'],
                    email=customer_data['email'],
                    address=customer_data['address'],
                    notes=customer_data['notes'],
                    created_by=customer_data['created_by']
                )
                
                customer = self.ticket_receipt.customer_service.create_customer(customer_dto)
                customer_id = customer.id
                self.refresh_customer_list(customer_id)
            
            # Create device
            technician_id = self.ticket_receipt.controls_section.technician_input.currentData()
            device_data = self.ticket_receipt.device_section.get_device_data(customer_id, technician_id)
            
            device_dto = self.ticket_receipt.device_service.create_device(
                device_data,
                current_user=self.ticket_receipt.user_id,
                ip_address='127.0.0.1'
            )
            
            # Create ticket
            ticket_data = {
                'device_id': device_dto.id,
                'created_by_id': self.ticket_receipt.user_id,
                **self.ticket_receipt.issue_section.get_issue_data(),
                **self.ticket_receipt.controls_section.get_controls_data()
            }
            
            # Set initial status based on technician assignment
            technician_id = self.ticket_receipt.controls_section.technician_input.currentData()
            ticket_data['status'] = "diagnosed" if technician_id else "open"
            
            ticket_dto = self.ticket_receipt.ticket_service.create_ticket(
                ticket_data,
                current_user=self.ticket_receipt.user_id,
                ip_address='127.0.0.1'
            )
            
            if self.print_chk.isChecked():
                print_data = self._gather_ticket_data_for_print(ticket_dto)
                self.print_generator.print_ticket(print_data)
            
            self.ticket_receipt.ticket_created.emit(ticket_dto)
            self.ticket_receipt.close()
            
        except Exception as e:
            self.handle_creation_error(e)
    
    def update_existing_ticket(self):
        """Update an existing ticket"""
        try:
            # Update customer if needed
            customer_data = self.ticket_receipt.customer_section.get_customer_data()
            if 'customer_id' not in customer_data:
                raise ValueError("Customer selection is required for updates")
            
            # Update device
            device_data = self.ticket_receipt.device_section.get_device_data(
                customer_data['customer_id'],
                self.ticket_receipt.controls_section.technician_input.currentData()
            )
            
            updated_device = self.ticket_receipt.device_service.update_device(
                self.ticket_receipt.current_ticket.device_id,
                device_data,
                current_user=self.ticket_receipt.user_id,
                ip_address='127.0.0.1'
            )
            
            if not updated_device:
                raise RuntimeError("Failed to update device information")
            
            # Update ticket
            ticket_data = {
                **self.ticket_receipt.issue_section.get_issue_data(),
                **self.ticket_receipt.controls_section.get_controls_data()
            }
            
            # Handle status changes based on technician assignment
            technician_id = self.ticket_receipt.controls_section.technician_input.currentData()
            current_status = self.ticket_receipt.current_ticket.status
            
            new_status = current_status
            if technician_id and current_status == "open":
                new_status = "diagnosed"
            elif not technician_id and current_status == "diagnosed":
                new_status = "open"
            
            ticket_data['status'] = new_status
            
            # Update device status if technician assignment changed
            if (technician_id and self.ticket_receipt.current_ticket.device and 
                self.ticket_receipt.current_ticket.device.status == "received"):
                device_status_data = {'status': 'diagnosed'}
                self.ticket_receipt.device_service.update_device(
                    self.ticket_receipt.current_ticket.device_id,
                    device_status_data,
                    current_user=self.ticket_receipt.user_id,
                    ip_address='127.0.0.1'
                )
            elif (not technician_id and self.ticket_receipt.current_ticket.device and 
                self.ticket_receipt.current_ticket.device.status == "diagnosed"):
                device_status_data = {'status': 'received'}
                self.ticket_receipt.device_service.update_device(
                    self.ticket_receipt.current_ticket.device_id,
                    device_status_data,
                    current_user=self.ticket_receipt.user_id,
                    ip_address='127.0.0.1'
                )
            
            updated_ticket = self.ticket_receipt.ticket_service.update_ticket(
                self.ticket_receipt.current_ticket.id,
                ticket_data,
                current_user=self.ticket_receipt.user_id,
                ip_address='127.0.0.1'
            )
            
            self.ticket_receipt.ticket_updated.emit(updated_ticket)
            
            if self.print_chk.isChecked():
                print_data = self._gather_ticket_data_for_print(updated_ticket)
                self.print_generator.print_ticket(print_data)
                
            self.ticket_receipt.close()
            
        except ValueError as e:
            MessageHandler.show_warning(self.ticket_receipt, self.lm.get("Tickets.validation_error", "Validation Error"), str(e))
        except RuntimeError as e:
            MessageHandler.show_critical(self.ticket_receipt, self.lm.get("Common.error", "Error"), str(e))
        except Exception as e:
            self.handle_update_error(e)
    
    def refresh_customer_list(self, customer_id):
        """Refresh customer list and select the specified customer"""
        self.ticket_receipt.customer_section.customer_search._load_customers()
        for i in range(self.ticket_receipt.customer_section.customer_search.customer_combo.count()):
            if self.ticket_receipt.customer_section.customer_search.customer_combo.itemData(i) == customer_id:
                self.ticket_receipt.customer_section.customer_search.customer_combo.setCurrentIndex(i)
                break
    
    def handle_creation_error(self, error):
        """Handle ticket creation errors"""
        MessageHandler.show_critical(self.ticket_receipt, self.lm.get("Common.error", "Error"), f"{self.lm.get('TicketMessages.update_failed', 'Failed to create ticket')}: {str(error)}")
    
    def handle_update_error(self, error):
        """Handle ticket update errors"""
        if "UNIQUE constraint failed" in str(error):
            MessageHandler.show_critical(
                self.ticket_receipt,
                "Update Error",
                "Failed to update ticket: A device with this IMEI already exists."
            )
        else:
            error_trace = traceback.format_exc()
            print(f"Update Error: {error_trace}")
            MessageHandler.show_critical(self.ticket_receipt, self.lm.get("Common.error", "Error"), f"{self.lm.get('TicketMessages.update_failed', 'Failed to update ticket')}: {str(error)}\n\nDebug Info:\n{error_trace}")
    
    def populate_form(self, ticket: TicketDTO):
        """Populate the form with existing ticket data"""
        # Customer - access through device relationship
        if ticket.device and ticket.device.customer_id:
            self.ticket_receipt.customer_section.customer_search.customer_combo.setCurrentIndex(
                self.ticket_receipt.customer_section.customer_search.customer_combo.findData(ticket.device.customer_id)
            )
        self.ticket_receipt.customer_section.fill_customer_details()
        
        # Device
        self.ticket_receipt.device_section.populate_form(ticket.device)
        
        # Issue details
        self.ticket_receipt.issue_section.populate_form(ticket)
        
        # Controls
        self.ticket_receipt.controls_section.populate_form(ticket)