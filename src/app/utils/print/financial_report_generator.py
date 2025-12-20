
import os
import platform
from datetime import datetime
from weasyprint import HTML
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter

class FinancialReportGenerator:
    def __init__(self, business_settings_service=None):
        self.lm = language_manager
        self.cf = currency_formatter
        # Placeholder for settings if needed
        self.business_name = "Mobile Service Accounting" 
        
    def generate_pdf(self, transactions, summary, start_date, end_date, filename):
        """Generate PDF report"""
        html = self._generate_html(transactions, summary, start_date, end_date)
        HTML(string=html).write_pdf(filename, presentational_hints=True)
        return filename

    def _generate_html(self, transactions, summary, start_date, end_date):
        font_family = "'Myanmar Text', 'Myanmar MN', 'Noto Sans Myanmar', 'Pyidaungsu', sans-serif"
        
        # Calculate totals
        total_income = summary.get('total_income', 0)
        total_expense = summary.get('total_expense', 0)
        net_balance = summary.get('net_balance', 0)
        
        # CSS
        style = f"""
        <style>
            @page {{ size: A4; margin: 1cm; }}
            body {{ font-family: {font_family}; font-size: 10pt; color: #333; }}
            .header {{ text-align: center; margin-bottom: 20px; }}
            .title {{ font-size: 16pt; font-weight: bold; color: #111; }}
            .subtitle {{ font-size: 10pt; color: #666; }}
            
            .summary-box {{ 
                display: flex; justify-content: space-between; 
                background-color: #f3f4f6; padding: 10px; margin-bottom: 20px; border-radius: 5px;
            }}
            .metric {{ text-align: center; width: 30%; }}
            .metric-label {{ font-size: 9pt; color: #666; }}
            .metric-val {{ font-size: 12pt; font-weight: bold; }}
            .inc {{ color: #10B981; }}
            .exp {{ color: #EF4444; }}
            
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th {{ background-color: #374151; color: white; padding: 8px; text-align: left; font-size: 9pt; }}
            td {{ border-bottom: 1px solid #e5e7eb; padding: 8px; font-size: 9pt; }}
            .amt {{ text-align: right; }}
            .row-inc {{ color: #047857; }}
            .row-exp {{ color: #B91C1C; }}
            
            .footer {{ margin-top: 30px; text-align: center; font-size: 8pt; color: #999; }}
        </style>
        """
        
        # HTML Content
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>{style}</head>
        <body>
            <div class="header">
                <div class="title">{self.lm.get('Financial.report_title', 'Financial Report')}</div>
                <div class="subtitle">{start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}</div>
            </div>
            
            <!-- Summary -->
            <table style="width:100%; margin-bottom: 20px;">
                <tr>
                    <td style="text-align: center; background-color: #ecfdf5; border: 1px solid #a7f3d0; padding: 10px;">
                        <div class="metric-label">{self.lm.get('Financial.income', 'Income')}</div>
                        <div class="metric-val inc">{self.cf.format(total_income)}</div>
                    </td>
                    <td style="width: 10px; border: none;"></td>
                    <td style="text-align: center; background-color: #fef2f2; border: 1px solid #fecaca; padding: 10px;">
                        <div class="metric-label">{self.lm.get('Financial.expense', 'Expense')}</div>
                        <div class="metric-val exp">{self.cf.format(total_expense)}</div>
                    </td>
                    <td style="width: 10px; border: none;"></td>
                    <td style="text-align: center; background-color: #eff6ff; border: 1px solid #bfdbfe; padding: 10px;">
                        <div class="metric-label">{self.lm.get('Financial.net_balance', 'Balance')}</div>
                        <div class="metric-val">{self.cf.format(net_balance)}</div>
                    </td>
                </tr>
            </table>
            
            <!-- Transactions Table -->
            <table>
                <thead>
                    <tr>
                        <th>{self.lm.get('Financial.date', 'Date')}</th>
                        <th>{self.lm.get('Financial.type', 'Type')}</th>
                        <th>{self.lm.get('Financial.category', 'Category')}</th>
                        <th>{self.lm.get('Financial.description', 'Description')}</th>
                        <th class="amt">{self.lm.get('Financial.amount', 'Amount')}</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for t in transactions:
            cat_name = t.category.name if t.category else "-"
            type_label = self.lm.get('Financial.type_income', 'Income') if t.type == 'income' else self.lm.get('Financial.type_expense', 'Expense')
            row_class = "row-inc" if t.type == 'income' else "row-exp"
            
            html += f"""
                <tr>
                    <td>{t.date.strftime('%Y-%m-%d')}</td>
                    <td class="{row_class}">{type_label}</td>
                    <td>{cat_name}</td>
                    <td>{t.description or ""}</td>
                    <td class="amt">{self.cf.format(t.amount)}</td>
                </tr>
            """
            
        html += """
                </tbody>
            </table>
            
            <div class="footer">
                Generated by Mobile Service Accounting on """ + datetime.now().strftime('%Y-%m-%d %H:%M') + """
            </div>
        </body>
        </html>
        """
        return html
