# src/app/utils/performance_export.py
"""
Performance Export Utility

Export technician performance data to PDF and Excel formats.
"""

from datetime import datetime, date
from decimal import Decimal
import csv
import io


class PerformanceExporter:
    """Utility for exporting performance data"""
    
    @staticmethod
    def export_to_csv(technician, performance_history, ytd_summary, filename):
        """Export performance data to CSV"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header
            writer.writerow(['Technician Performance Report'])
            writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow([])
            
            # Technician Info
            writer.writerow(['Technician Information'])
            writer.writerow(['Name:', technician.full_name])
            writer.writerow(['Email:', technician.email or 'N/A'])
            writer.writerow(['Phone:', technician.phone or 'N/A'])
            writer.writerow(['Specialization:', technician.specialization or 'N/A'])
            writer.writerow(['Base Salary:', f'${float(technician.salary):,.2f}'])
            writer.writerow(['Commission Rate:', f'{float(technician.commission_rate)}%'])
            writer.writerow([])
            
            # YTD Summary
            writer.writerow(['Year-to-Date Summary'])
            writer.writerow(['Total Tickets:', ytd_summary['total_tickets']])
            writer.writerow(['Total Revenue:', f'${ytd_summary["total_revenue"]:,.2f}'])
            writer.writerow(['Total Commission:', f'${ytd_summary["total_commission"]:,.2f}'])
            writer.writerow(['Total Bonuses:', f'${ytd_summary["total_bonuses"]:,.2f}'])
            writer.writerow(['Avg Completion Days:', f'{ytd_summary["avg_completion_days"]:.2f}'])
            writer.writerow(['Avg Efficiency:', f'{ytd_summary["avg_efficiency"]:.2f}'])
            writer.writerow([])
            
            # Monthly Performance
            writer.writerow(['Monthly Performance History'])
            writer.writerow([
                'Month', 'Tickets Completed', 'Tickets Pending', 
                'Revenue', 'Commission', 'Bonuses', 
                'Efficiency', 'Avg Completion Days'
            ])
            
            for perf in performance_history:
                writer.writerow([
                    perf.month.strftime('%B %Y'),
                    perf.tickets_completed,
                    perf.tickets_pending,
                    f'${float(perf.revenue_generated):,.2f}',
                    f'${float(perf.commission_earned):,.2f}',
                    f'${float(perf.bonuses_earned):,.2f}',
                    f'{float(perf.efficiency_score):.2f}',
                    f'{float(perf.avg_completion_days):.2f}'
                ])
        
        return filename
    
    @staticmethod
    def export_bonus_history_to_csv(technician, bonuses, filename):
        """Export bonus history to CSV"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header
            writer.writerow(['Technician Bonus History'])
            writer.writerow(['Technician:', technician.full_name])
            writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow([])
            
            # Bonus data
            writer.writerow([
                'Date Awarded', 'Bonus Type', 'Amount', 'Reason', 
                'Period Start', 'Period End', 'Paid', 'Paid Date'
            ])
            
            for bonus in bonuses:
                writer.writerow([
                    bonus.awarded_date.strftime('%Y-%m-%d'),
                    bonus.bonus_type.title(),
                    f'${float(bonus.amount):,.2f}',
                    bonus.reason or '',
                    bonus.period_start.strftime('%Y-%m-%d') if bonus.period_start else 'N/A',
                    bonus.period_end.strftime('%Y-%m-%d') if bonus.period_end else 'N/A',
                    'Yes' if bonus.paid else 'No',
                    bonus.paid_date.strftime('%Y-%m-%d') if bonus.paid_date else 'N/A'
                ])
            
            # Summary
            writer.writerow([])
            total = sum(Decimal(str(b.amount)) for b in bonuses)
            paid = sum(Decimal(str(b.amount)) for b in bonuses if b.paid)
            unpaid = total - paid
            
            writer.writerow(['Summary'])
            writer.writerow(['Total Bonuses:', f'${total:,.2f}'])
            writer.writerow(['Paid:', f'${paid:,.2f}'])
            writer.writerow(['Unpaid:', f'${unpaid:,.2f}'])
        
        return filename
    
    @staticmethod
    def export_team_comparison_to_csv(comparison_data, month, filename):
        """Export team comparison to CSV"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header
            writer.writerow(['Team Performance Comparison'])
            writer.writerow(['Month:', month.strftime('%B %Y')])
            writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow([])
            
            # Data
            writer.writerow([
                'Rank', 'Technician', 'Tickets Completed', 
                'Revenue Generated', 'Commission Earned', 
                'Efficiency Score', 'Avg Completion Days'
            ])
            
            for rank, data in enumerate(comparison_data, 1):
                writer.writerow([
                    rank,
                    data['technician_name'],
                    data['tickets_completed'],
                    f'${float(data["revenue_generated"]):,.2f}',
                    f'${float(data["commission_earned"]):,.2f}',
                    f'{float(data["efficiency_score"]):.2f}',
                    f'{float(data["avg_completion_days"]):.2f}'
                ])
        
        return filename
    
    @staticmethod
    def generate_monthly_report_text(technician, performance, bonuses):
        """Generate a text-based monthly report"""
        report = []
        report.append("=" * 60)
        report.append("MONTHLY PERFORMANCE REPORT")
        report.append("=" * 60)
        report.append("")
        report.append(f"Technician: {technician.full_name}")
        report.append(f"Month: {performance.month.strftime('%B %Y')}")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        report.append("-" * 60)
        report.append("PERFORMANCE METRICS")
        report.append("-" * 60)
        report.append(f"Tickets Completed:      {performance.tickets_completed}")
        report.append(f"Tickets Pending:        {performance.tickets_pending}")
        report.append(f"Avg Completion Time:    {float(performance.avg_completion_days):.2f} days")
        report.append(f"Efficiency Score:       {float(performance.efficiency_score):.2f}")
        report.append("")
        report.append("-" * 60)
        report.append("FINANCIAL SUMMARY")
        report.append("-" * 60)
        report.append(f"Revenue Generated:      ${float(performance.revenue_generated):,.2f}")
        report.append(f"Commission Earned:      ${float(performance.commission_earned):,.2f}")
        report.append(f"Bonuses Earned:         ${float(performance.bonuses_earned):,.2f}")
        report.append("")
        
        # Compensation breakdown
        base = Decimal(str(technician.salary))
        commission = Decimal(str(performance.commission_earned))
        bonus_total = Decimal(str(performance.bonuses_earned))
        total = base + commission + bonus_total
        
        report.append("-" * 60)
        report.append("COMPENSATION BREAKDOWN")
        report.append("-" * 60)
        report.append(f"Base Salary:            ${base:,.2f}")
        report.append(f"Commission:             ${commission:,.2f}")
        report.append(f"Bonuses:                ${bonus_total:,.2f}")
        report.append(f"{'TOTAL COMPENSATION:':20s}${total:,.2f}")
        report.append("")
        
        # Bonuses detail
        if bonuses:
            report.append("-" * 60)
            report.append("BONUSES AWARDED THIS MONTH")
            report.append("-" * 60)
            for bonus in bonuses:
                report.append(f"{bonus.bonus_type.title():15s} ${float(bonus.amount):>10,.2f}  {bonus.reason or ''}")
            report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)
