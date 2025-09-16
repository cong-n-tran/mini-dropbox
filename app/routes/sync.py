"""
File synchronization and notification routes
"""

from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_socketio import emit, join_room, leave_room
from app import db, socketio
from app.models import User, SyncEvent, Device

sync_bp = Blueprint('sync', __name__)


@sync_bp.route('/events', methods=['GET'])
@jwt_required()
def get_sync_events():
    """Get sync events for the user"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get query parameters
        since = request.args.get('since')
        device_id = request.args.get('device_id')
        limit = min(request.args.get('limit', 100, type=int), 500)
        
        # Build query
        query = SyncEvent.query.filter_by(user_id=current_user_id)
        
        # Filter by timestamp
        if since:
            try:
                since_datetime = datetime.fromisoformat(since.replace('Z', '+00:00'))
                query = query.filter(SyncEvent.created_at > since_datetime)
            except ValueError:
                return jsonify({'error': 'Invalid since parameter format'}), 400
        
        # Exclude events from the same device to avoid loops
        if device_id:
            query = query.filter(SyncEvent.device_id != device_id)
        
        # Order by created_at and limit
        events = query.order_by(SyncEvent.created_at.desc()).limit(limit).all()
        
        return jsonify({
            'events': [event.to_dict() for event in events],
            'count': len(events)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get sync events'}), 500


@sync_bp.route('/events/<int:event_id>/processed', methods=['PUT'])
@jwt_required()
def mark_event_processed(event_id):
    """Mark a sync event as processed"""
    try:
        current_user_id = get_jwt_identity()
        
        event = SyncEvent.query.filter_by(
            id=event_id,
            user_id=current_user_id
        ).first()
        
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        
        event.processed = True
        db.session.commit()
        
        return jsonify({'message': 'Event marked as processed'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to mark event as processed'}), 500


@sync_bp.route('/status', methods=['GET'])
@jwt_required()
def get_sync_status():
    """Get synchronization status"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get device sync status
        devices = Device.query.filter_by(
            user_id=current_user_id,
            is_active=True
        ).all()
        
        # Get recent sync events count
        recent_events = SyncEvent.query.filter_by(
            user_id=current_user_id
        ).filter(
            SyncEvent.created_at > datetime.utcnow() - timedelta(hours=24)
        ).count()
        
        # Get unprocessed events count
        unprocessed_events = SyncEvent.query.filter_by(
            user_id=current_user_id,
            processed=False
        ).count()
        
        return jsonify({
            'user_id': current_user_id,
            'devices': [device.to_dict() for device in devices],
            'recent_events_24h': recent_events,
            'unprocessed_events': unprocessed_events,
            'storage_used': user.storage_used,
            'storage_quota': user.storage_quota,
            'last_sync': max([device.last_sync for device in devices]) if devices else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get sync status'}), 500


@sync_bp.route('/ping', methods=['POST'])
@jwt_required()
def sync_ping():
    """Update device last sync timestamp"""
    try:
        current_user_id = get_jwt_identity()
        device_id = request.headers.get('X-Device-ID')
        
        if not device_id:
            return jsonify({'error': 'Device ID required'}), 400
        
        device = Device.query.filter_by(
            user_id=current_user_id,
            device_id=device_id
        ).first()
        
        if device:
            device.last_sync = datetime.utcnow()
            db.session.commit()
        
        return jsonify({'message': 'Sync ping recorded'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to record sync ping'}), 500


# WebSocket events for real-time synchronization
@socketio.on('connect')
@jwt_required()
def handle_connect():
    """Handle client connection"""
    try:
        current_user_id = get_jwt_identity()
        join_room(f'user_{current_user_id}')
        emit('connected', {'message': 'Connected to sync channel'})
    except Exception as e:
        emit('error', {'message': 'Authentication failed'})


@socketio.on('disconnect')
@jwt_required()
def handle_disconnect():
    """Handle client disconnection"""
    try:
        current_user_id = get_jwt_identity()
        leave_room(f'user_{current_user_id}')
    except Exception:
        pass


@socketio.on('join_sync_room')
@jwt_required()
def handle_join_sync_room(data):
    """Join sync room for real-time updates"""
    try:
        current_user_id = get_jwt_identity()
        device_id = data.get('device_id')
        
        if device_id:
            # Update device last sync
            device = Device.query.filter_by(
                user_id=current_user_id,
                device_id=device_id
            ).first()
            
            if device:
                device.last_sync = datetime.utcnow()
                db.session.commit()
        
        join_room(f'user_{current_user_id}')
        emit('joined_sync_room', {
            'message': 'Joined sync room',
            'user_id': current_user_id,
            'device_id': device_id
        })
        
    except Exception as e:
        emit('error', {'message': 'Failed to join sync room'})


@socketio.on('leave_sync_room')
@jwt_required()
def handle_leave_sync_room():
    """Leave sync room"""
    try:
        current_user_id = get_jwt_identity()
        leave_room(f'user_{current_user_id}')
        emit('left_sync_room', {'message': 'Left sync room'})
    except Exception:
        pass


@socketio.on('request_sync')
@jwt_required()
def handle_request_sync(data):
    """Handle sync request from client"""
    try:
        current_user_id = get_jwt_identity()
        device_id = data.get('device_id')
        last_sync = data.get('last_sync')
        
        # Get events since last sync
        query = SyncEvent.query.filter_by(user_id=current_user_id)
        
        if last_sync:
            try:
                last_sync_datetime = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
                query = query.filter(SyncEvent.created_at > last_sync_datetime)
            except ValueError:
                pass
        
        # Exclude events from the same device
        if device_id:
            query = query.filter(SyncEvent.device_id != device_id)
        
        events = query.order_by(SyncEvent.created_at.asc()).limit(100).all()
        
        emit('sync_events', {
            'events': [event.to_dict() for event in events],
            'count': len(events),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        emit('error', {'message': 'Failed to process sync request'})


# Helper function to broadcast sync events
def broadcast_sync_event(user_id, event_type, data, exclude_device=None):
    """Broadcast sync event to user's devices"""
    try:
        socketio.emit('sync_event', {
            'event_type': event_type,
            'data': data,
            'timestamp': datetime.utcnow().isoformat(),
            'exclude_device': exclude_device
        }, room=f'user_{user_id}')
    except Exception:
        pass