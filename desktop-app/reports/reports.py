from datetime import datetime, timedelta
import sqlite3
from typing import List, Dict, Tuple
import calendar
from decimal import Decimal

class FinancialReports:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.conn = sqlite3.connect('budget.db')
        self.cursor = self.conn.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()

    def monthly_summary(self, year: int, month: int) -> Dict:
        """
        Generuje miesięczne podsumowanie finansów
        - Suma przychodów i wydatków
        - Bilans
        - Top 5 kategorii wydatków
        - Top 3 kategorie przychodów
        """
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]}"
        
        self.cursor.execute("""
            SELECT 
                t.type,
                c.name as category,
                SUM(t.amount) as total,
                COUNT(*) as count
            FROM transactions t
            JOIN categories c ON t.category_id = c.category_id
            JOIN accounts a ON t.account_id = a.account_id
            WHERE a.user_id = ? 
            AND t.transaction_date BETWEEN ? AND ?
            GROUP BY t.type, c.name
            ORDER BY t.type, total DESC
        """, (self.user_id, start_date, end_date))
        
        results = self.cursor.fetchall()
        
        summary = {
            'period': f"{calendar.month_name[month]} {year}",
            'income': {'total': 0, 'by_category': []},
            'outcome': {'total': 0, 'by_category': []},
            'balance': 0
        }
        
        for type_, category, total, count in results:
            if type_ == 'income':
                summary['income']['total'] += total
                summary['income']['by_category'].append({
                    'category': category,
                    'amount': total,
                    'count': count
                })
            else:
                summary['outcome']['total'] += total
                summary['outcome']['by_category'].append({
                    'category': category,
                    'amount': total,
                    'count': count
                })
        
        summary['balance'] = summary['income']['total'] - summary['outcome']['total']
        return summary

    def spending_trends(self, months: int = 6) -> List[Dict]:
        """
        Analizuje trendy wydatków w ostatnich X miesiącach
        - Miesięczne wydatki w kategoriach
        - Porównanie z poprzednimi miesiącami
        - Identyfikacja wzrostów/spadków
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30 * months)
        
        self.cursor.execute("""
            SELECT 
                strftime('%Y-%m', t.transaction_date) as month,
                c.name as category,
                t.type,
                SUM(t.amount) as total
            FROM transactions t
            JOIN categories c ON t.category_id = c.category_id
            JOIN accounts a ON t.account_id = a.account_id
            WHERE a.user_id = ? 
            AND t.transaction_date BETWEEN ? AND ?
            GROUP BY month, c.name, t.type
            ORDER BY month DESC, t.type, total DESC
        """, (self.user_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
        
        return self._format_trends(self.cursor.fetchall())

    def savings_analysis(self) -> Dict:
        """
        Analiza oszczędności
        - Miesięczne oszczędności (przychody - wydatki)
        - Projekcja oszczędności
        - Analiza kategorii z potencjałem oszczędności
        """
        self.cursor.execute("""
            WITH monthly_totals AS (
                SELECT 
                    strftime('%Y-%m', t.transaction_date) as month,
                    t.type,
                    SUM(t.amount) as total
                FROM transactions t
                JOIN accounts a ON t.account_id = a.account_id
                WHERE a.user_id = ?
                GROUP BY month, t.type
            )
            SELECT 
                month,
                MAX(CASE WHEN type = 'income' THEN total ELSE 0 END) as income,
                MAX(CASE WHEN type = 'outcome' THEN total ELSE 0 END) as outcome
            FROM monthly_totals
            GROUP BY month
            ORDER BY month DESC
            LIMIT 12
        """, (self.user_id,))
        
        return self._calculate_savings(self.cursor.fetchall())

    def budget_recommendations(self) -> Dict:
        """
        Generuje rekomendacje budżetowe
        - Identyfikacja kategorii z największymi wydatkami
        - Porównanie z średnimi wydatkami
        - Sugestie oszczędności
        """
        # Analiza ostatnich 3 miesięcy
        three_months_ago = datetime.now() - timedelta(days=90)
        
        self.cursor.execute("""
            SELECT 
                c.name as category,
                AVG(t.amount) as avg_amount,
                COUNT(*) as transaction_count,
                SUM(t.amount) as total_amount
            FROM transactions t
            JOIN categories c ON t.category_id = c.category_id
            JOIN accounts a ON t.account_id = a.account_id
            WHERE a.user_id = ? 
            AND t.type = 'outcome'
            AND t.transaction_date >= ?
            GROUP BY c.name
            HAVING COUNT(*) > 5
            ORDER BY total_amount DESC
        """, (self.user_id, three_months_ago.strftime('%Y-%m-%d')))
        
        return self._generate_recommendations(self.cursor.fetchall())

    def account_balance_history(self, account_id: int = None) -> List[Dict]:
        """
        Historia sald na kontach
        - Dzienny bilans
        - Skumulowane saldo
        - Analiza przepływów
        """
        query = """
            SELECT 
                date(t.transaction_date) as date,
                a.account_name,
                a.currency_id,
                SUM(CASE WHEN t.type = 'income' THEN t.amount ELSE -t.amount END) as daily_change
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            WHERE a.user_id = ?
        """
        params = [self.user_id]
        
        if account_id:
            query += " AND a.account_id = ?"
            params.append(account_id)
            
        query += """
            GROUP BY date, a.account_id
            ORDER BY date
        """
        
        self.cursor.execute(query, params)
        return self._calculate_balance_history(self.cursor.fetchall())

    def category_analysis(self, category_id: int = None) -> Dict:
        """
        Szczegółowa analiza kategorii
        - Statystyki transakcji
        - Średnie wartości
        - Trendy czasowe
        """
        six_months_ago = datetime.now() - timedelta(days=180)
        
        query = """
            SELECT 
                c.name,
                t.type,
                strftime('%Y-%m', t.transaction_date) as month,
                COUNT(*) as transaction_count,
                AVG(t.amount) as avg_amount,
                MIN(t.amount) as min_amount,
                MAX(t.amount) as max_amount,
                SUM(t.amount) as total_amount
            FROM transactions t
            JOIN categories c ON t.category_id = c.category_id
            JOIN accounts a ON t.account_id = a.account_id
            WHERE a.user_id = ?
            AND t.transaction_date >= ?
        """
        params = [self.user_id, six_months_ago.strftime('%Y-%m-%d')]
        
        if category_id:
            query += " AND c.category_id = ?"
            params.append(category_id)
            
        query += """
            GROUP BY c.name, t.type, month
            ORDER BY month DESC, c.name
        """
        
        self.cursor.execute(query, params)
        return self._format_category_analysis(self.cursor.fetchall())

    def _format_trends(self, data: List[Tuple]) -> List[Dict]:
        """Formatuje dane trendów"""
        trends = []
        current_month = None
        month_data = None
        
        for month, category, type_, total in data:
            if month != current_month:
                if month_data:
                    trends.append(month_data)
                current_month = month
                month_data = {
                    'month': month,
                    'income': [],
                    'outcome': [],
                    'total_income': 0,
                    'total_outcome': 0
                }
            
            if type_ == 'income':
                month_data['income'].append({'category': category, 'amount': total})
                month_data['total_income'] += total
            else:
                month_data['outcome'].append({'category': category, 'amount': total})
                month_data['total_outcome'] += total
        
        if month_data:
            trends.append(month_data)
        
        return trends

    def _calculate_savings(self, data: List[Tuple]) -> Dict:
        """Oblicza statystyki oszczędności"""
        savings = {
            'monthly_savings': [],
            'total_savings': 0,
            'average_monthly_saving': 0,
            'best_month': None,
            'worst_month': None
        }
        
        total_months = 0
        best_saving = float('-inf')
        worst_saving = float('inf')
        
        for month, income, outcome in data:
            saving = income - outcome
            savings['monthly_savings'].append({
                'month': month,
                'income': income,
                'outcome': outcome,
                'saving': saving
            })
            
            savings['total_savings'] += saving
            total_months += 1
            
            if saving > best_saving:
                best_saving = saving
                savings['best_month'] = {'month': month, 'amount': saving}
            
            if saving < worst_saving:
                worst_saving = saving
                savings['worst_month'] = {'month': month, 'amount': saving}
        
        if total_months > 0:
            savings['average_monthly_saving'] = savings['total_savings'] / total_months
        
        return savings

    def _generate_recommendations(self, data: List[Tuple]) -> Dict:
        """Generuje rekomendacje oszczędnościowe"""
        recommendations = {
            'high_spending_categories': [],
            'potential_savings': [],
            'general_recommendations': []
        }
        
        total_spending = sum(total for _, _, _, total in data)
        
        for category, avg_amount, count, total in data:
            percentage = (total / total_spending) * 100
            
            if percentage > 20:
                recommendations['high_spending_categories'].append({
                    'category': category,
                    'percentage': percentage,
                    'average_transaction': avg_amount,
                    'total': total,
                    'recommendation': f"Rozważ ograniczenie wydatków w kategorii {category}"
                })
            
            if avg_amount > 100 and count > 10:
                potential_saving = avg_amount * 0.1 * count
                recommendations['potential_savings'].append({
                    'category': category,
                    'potential_monthly_saving': potential_saving,
                    'suggestion': f"Zmniejsz średnią wartość transakcji o 10%"
                })
        
        return recommendations

    def _calculate_balance_history(self, data: List[Tuple]) -> List[Dict]:
        """Oblicza historię sald"""
        balance_history = []
        current_balance = 0
        
        for date, account_name, currency, daily_change in data:
            current_balance += daily_change
            balance_history.append({
                'date': date,
                'account': account_name,
                'currency': currency,
                'daily_change': daily_change,
                'balance': current_balance
            })
        
        return balance_history

    def _format_category_analysis(self, data: List[Tuple]) -> Dict:
        """Formatuje analizę kategorii"""
        analysis = {
            'monthly_stats': {},
            'overall_stats': {
                'total_transactions': 0,
                'total_amount': 0,
                'average_transaction': 0
            }
        }
        
        for name, type_, month, count, avg, min_, max_, total in data:
            if month not in analysis['monthly_stats']:
                analysis['monthly_stats'][month] = {
                    'income': [],
                    'outcome': []
                }
            
            category_stats = {
                'category': name,
                'transaction_count': count,
                'average_amount': avg,
                'min_amount': min_,
                'max_amount': max_,
                'total_amount': total
            }
            
            if type_ == 'income':
                analysis['monthly_stats'][month]['income'].append(category_stats)
            else:
                analysis['monthly_stats'][month]['outcome'].append(category_stats)
            
            analysis['overall_stats']['total_transactions'] += count
            analysis['overall_stats']['total_amount'] += total
        
        if analysis['overall_stats']['total_transactions'] > 0:
            analysis['overall_stats']['average_transaction'] = (
                analysis['overall_stats']['total_amount'] / 
                analysis['overall_stats']['total_transactions']
            )
        
        return analysis

#</rewritten_file>