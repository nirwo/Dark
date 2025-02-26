from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, Response
from flask_login import login_required, current_user
from sqlalchemy import desc
import time
import json
import csv
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import os
import datetime
import logging

from models import db, SearchHistory

# Create a logger
logger = logging.getLogger(__name__)

# Create history blueprint
history = Blueprint('history', __name__)

@history.route('/history')
@login_required
def view_history():
    """View search history for the current user"""
    try:
        # Fetch search history for the current user
        searches = SearchHistory.query.filter_by(user_id=current_user.id).order_by(desc(SearchHistory.timestamp)).all()
        
        # Process the search history for display
        history_items = []
        for search in searches:
            # Handle both old and new database structures
            identifier = getattr(search, 'search_query', None) or getattr(search, 'email_searched', 'Unknown')
            search_type = getattr(search, 'search_type', 'email')
            
            # Try to get breach counts by category from results
            breach_categories = {"credentials": 0, "personal": 0, "financial": 0, "other": 0}
            
            if search.results_json:
                try:
                    results_data = json.loads(search.results_json)
                    
                    # Extract breach categories
                    if isinstance(results_data, dict) and 'results' in results_data:
                        for site_data in results_data['results'].values():
                            breaches = site_data.get('breach_details', {})
                            for category, count in breach_categories.items():
                                breach_categories[category] += len(breaches.get(category, []))
                    elif isinstance(results_data, list):
                        for result in results_data:
                            breaches = result.get('breach_details', {})
                            for category, count in breach_categories.items():
                                breach_categories[category] += len(breaches.get(category, []))
                except Exception as e:
                    flash(f"Error processing results: {str(e)}", "error")
                    logger.error(f"Error processing search results: {str(e)}")
            
            # Build history item
            history_item = {
                'id': search.id,
                'query': identifier,
                'search_type': search_type,
                'timestamp': search.timestamp,
                'result_count': search.result_count,
                'risk_level': search.risk_level,
                'breach_categories': breach_categories
            }
            
            history_items.append(history_item)
        
        return render_template('history.html', history_items=history_items)
    except Exception as e:
        flash(f"Error fetching history: {str(e)}", "error")
        logger.error(f"Error in view_history: {str(e)}")
        return render_template('history.html', history_items=[])

@history.route('/history/<int:search_id>')
@login_required
def view_search_details(search_id):
    """View details of a specific search"""
    try:
        # Get the search details
        search = SearchHistory.query.filter_by(id=search_id, user_id=current_user.id).first_or_404()
        
        # Handle both old and new database structures
        identifier = getattr(search, 'search_query', None) or getattr(search, 'email_searched', 'Unknown')
        search_type = getattr(search, 'search_type', 'email')
        
        # Process the results for display
        results_data = {}
        if search.results_json:
            try:
                results_data = json.loads(search.results_json)
            except json.JSONDecodeError:
                flash("Error decoding search results", "error")
                results_data = {"results": {}}
        
        # Format the results for the template
        if isinstance(results_data, dict) and 'results' in results_data:
            formatted_results = results_data
        else:
            # Format list-style results into the expected structure
            formatted_results = {"results": {}}
            if isinstance(results_data, list):
                for idx, item in enumerate(results_data):
                    site_name = item.get('source', f'Source {idx+1}')
                    formatted_results["results"][site_name] = item
        
        return render_template('search_details.html', search=search, results=formatted_results)
    except Exception as e:
        flash(f"Error viewing search details: {str(e)}", "error")
        logger.error(f"Error in view_search_details: {str(e)}")
        return redirect(url_for('history.view_history'))

@history.route('/history/delete/<int:search_id>', methods=['POST'])
@login_required
def delete_search(search_id):
    """Delete a search from history"""
    search = SearchHistory.query.get_or_404(search_id)
    
    # Check if the search belongs to the current user or if the user is an admin
    if search.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to delete this search.')
        return redirect(url_for('history.view_history'))
    
    db.session.delete(search)
    db.session.commit()
    
    flash('Search deleted successfully.')
    return redirect(url_for('history.view_history'))

@history.route('/admin/history')
@login_required
def admin_history():
    """Admin view of all users' search history"""
    if not current_user.is_admin:
        flash('You do not have permission to access this page.')
        return redirect(url_for('index'))
    
    searches = SearchHistory.query.order_by(desc(SearchHistory.timestamp)).all()
    return render_template('admin_history.html', searches=searches)

@history.route('/export/history/<int:search_id>')
@login_required
def export_search(search_id):
    """Export search results"""
    search = SearchHistory.query.get_or_404(search_id)
    
    # Check if the search belongs to the current user or if the user is an admin
    if search.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to export this search.')
        return redirect(url_for('history.view_history'))
    
    # Get export format from query parameters, default to JSON
    export_format = request.args.get('format', 'json').lower()
    
    if export_format == 'csv':
        return export_as_csv(search)
    elif export_format == 'pdf':
        return export_as_pdf(search)
    else:
        # Default to JSON export
        response = jsonify(search.get_results())
        response.headers.set('Content-Disposition', f'attachment; filename=search_{search_id}_{search.search_query}.json')
        response.headers.set('Content-Type', 'application/json')
        return response


@history.route('/export/history/<int:search_id>/csv')
@login_required
def export_search_csv(search_id):
    """Export search results as CSV (convenience route)"""
    return redirect(url_for('history.export_search', search_id=search_id, format='csv'))


@history.route('/export/history/<int:search_id>/pdf')
@login_required
def export_search_pdf(search_id):
    """Export search results as PDF (convenience route)"""
    return redirect(url_for('history.export_search', search_id=search_id, format='pdf'))


def export_as_csv(search):
    """Generate CSV export from search results"""
    results = search.get_results()
    output = io.StringIO()
    csv_writer = csv.writer(output)
    
    # Write header row
    csv_writer.writerow(['Search Query', 'Site', 'Risk Level', 'Description', 'Mention Context', 'Date'])
    
    # Write data rows
    search_query = search.search_query
    if results and 'results' in results:
        for site_name, site_data in results['results'].items():
            risk_level = site_data.get('risk_level', 'medium')
            description = site_data.get('description', 'No description available')
            
            if 'mentions' in site_data and site_data['mentions']:
                for mention in site_data['mentions']:
                    context = mention.get('context', 'Context not available')
                    date = mention.get('date', 'Date unknown')
                    csv_writer.writerow([search_query, site_name, risk_level, description, context, date])
            else:
                # If no mentions, write at least the site info
                csv_writer.writerow([search_query, site_name, risk_level, description, 'No mentions', 'N/A'])
    
    # Prepare the response
    output.seek(0)
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers.set('Content-Disposition', f'attachment; filename=search_{search.id}_{search.search_query}.csv')
    
    return response

def export_as_pdf(search):
    """Generate PDF export from search results"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Title'],
        fontSize=16,
        spaceAfter=20
    )
    
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=10
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    
    # Build story content
    story = []
    
    # Add title
    story.append(Paragraph(f"Dark Web Scanner Report", title_style))
    story.append(Paragraph(f"Search Query: {search.search_query}", subtitle_style))
    
    # Add metadata
    meta_data = [
        ['Date', search.timestamp.strftime('%Y-%m-%d %H:%M')],
        ['Risk Level', search.risk_level.title()],
        ['Results Found', str(search.result_count)],
        ['Duration', f"{search.search_duration:.2f} seconds"]
    ]
    
    meta_table = Table(meta_data, colWidths=[1.5*inch, 4*inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(meta_table)
    story.append(Spacer(1, 20))
    
    # Add results
    results = search.get_results()
    if results and 'results' in results:
        story.append(Paragraph("Detailed Findings", subtitle_style))
        
        # Sort results by risk level
        risk_order = {'critical': 0, 'high': 1, 'medium-high': 2, 'medium': 3, 'low': 4}
        sorted_results = sorted(
            results['results'].items(),
            key=lambda x: risk_order.get(x[1].get('risk_level', 'medium'), 3)
        )
        
        for site_name, site_data in sorted_results:
            # Site header
            risk_level = site_data.get('risk_level', 'medium').title()
            site_header = f"{site_name} - {risk_level} Risk"
            story.append(Paragraph(site_header, subtitle_style))
            
            # Site description
            description = site_data.get('description', 'No additional information available.')
            story.append(Paragraph(description, normal_style))
            story.append(Spacer(1, 10))
            
            # Mentions
            if 'mentions' in site_data and site_data['mentions']:
                mention_data = [['Context', 'Date']]
                for mention in site_data['mentions']:
                    mention_data.append([
                        mention.get('context', 'Context not available'),
                        mention.get('date', 'Date unknown')
                    ])
                
                mention_table = Table(mention_data, colWidths=[4*inch, 1.5*inch])
                mention_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('PADDING', (0, 0), (-1, -1), 6),
                ]))
                
                story.append(mention_table)
            else:
                story.append(Paragraph("No specific mentions found.", normal_style))
            
            story.append(Spacer(1, 15))
    
    # Build the PDF
    doc.build(story)
    
    # Prepare the response
    buffer.seek(0)
    response = Response(buffer.getvalue(), mimetype='application/pdf')
    response.headers.set('Content-Disposition', f'attachment; filename=search_{search.id}_{search.search_query}.pdf')
    
    return response

@history.route('/record', methods=['POST'])
@login_required
def record_search():
    """Record a search in the database"""
    if not current_user.is_authenticated:
        return jsonify({"status": "error", "message": "You must be logged in to record searches"}), 403

    data = request.get_json()
    email = data.get('email')
    query = data.get('query')
    search_type = data.get('search_type', 'email')
    
    results_data = data.get('results', [])
    search_duration = data.get('duration', 0)
    
    # Calculate result count and highest risk level
    result_count = len(results_data)
    highest_risk = 'low'
    risk_levels = {'critical': 4, 'high': 3, 'medium-high': 2, 'medium': 1, 'low': 0}
    
    # Determine highest risk level
    if isinstance(results_data, dict) and 'results' in results_data:
        result_count = len(results_data['results'])
        for site_data in results_data['results'].values():
            site_risk = site_data.get('risk_level', 'low')
            if risk_levels.get(site_risk, 0) > risk_levels.get(highest_risk, 0):
                highest_risk = site_risk
    elif isinstance(results_data, list):
        for item in results_data:
            item_risk = item.get('risk_level', 'low')
            if risk_levels.get(item_risk, 0) > risk_levels.get(highest_risk, 0):
                highest_risk = item_risk
    
    # Create a new search history entry
    search = SearchHistory(
        user_id=current_user.id,
        result_count=result_count,
        risk_level=highest_risk,
        results_json=json.dumps(results_data),
        search_duration=search_duration
    )
    
    # Handle both new and old database structures
    if hasattr(search, 'search_query'):
        search.search_query = query or email
        search.search_type = search_type
    else:
        search.email_searched = email
    
    db.session.add(search)
    db.session.commit()
    
    return jsonify({"status": "success", "id": search.id})
