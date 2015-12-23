#!/usr/bin/env python3

#
# Copyright (c) 2015, Christopher Atherton <the8lack8ox@gmail.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

import os
import re
import sys
import time

import argparse
import datetime
import imghdr

ID3V1_GENRES=(
	'Blues', 'ClassicRock', 'Country', 'Dance', 'Disco', 'Funk', 'Grunge',
	'Hip-Hop', 'Jazz', 'Metal', 'NewAge', 'Oldies', 'Other', 'Pop', 'R&B',
	'Rap', 'Reggae', 'Rock', 'Techno', 'Industrial', 'Alternative', 'Ska',
	'DeathMetal', 'Pranks', 'Soundtrack', 'Euro-Techno', 'Ambient', 'Trip-Hop',
	'Vocal', 'Jazz+Funk', 'Fusion', 'Trance', 'Classical', 'Instrumental',
	'Acid', 'House', 'Game', 'SoundClip', 'Gospel', 'Noise', 'AlternativeRock',
	'Bass', 'Soul', 'Punk', 'Space', 'Meditative', 'InstrumentalPop',
	'InstrumentalRock', 'Ethnic', 'Gothic', 'Darkwave', 'Techno-Industrial',
	'Electronic', 'Pop-Folk', 'Eurodance', 'Dream', 'SouthernRock', 'Comedy',
	'Cult', 'GangstaRap', 'Top40', 'ChristianRap', 'Pop/Funk', 'Jungle',
	'NativeAmerican', 'Cabaret', 'NewWave', 'Psychadelic', 'Rave', 'Showtunes',
	'Trailer', 'Lo-Fi', 'Tribal', 'AcidPunk', 'AcidJazz', 'Polka', 'Retro',
	'Musical', 'Rock&Roll', 'HardRock', 'Folk', 'Folk-Rock', 'NationalFolk',
	'Swing', 'FastFusion', 'Bebob', 'Latin', 'Revival', 'Celtic', 'Bluegrass',
	'Avantgarde', 'GothicRock', 'ProgressiveRock', 'PsychedelicRock',
	'SymphonicRock', 'SlowRock', 'BigBand', 'Chorus', 'EasyListening',
	'Acoustic', 'Humor', 'Speech', 'Chanson', 'Opera', 'ChamberMusic',
	'Sonata', 'Symphony', 'BootyBass', 'Primus', 'PornGroove', 'Satire',
	'SlowJam', 'Club', 'Tango', 'Samba', 'Folklore', 'Ballad', 'PowerBallad',
	'RhythmicSoul', 'Freestyle', 'Duet', 'PunkRock', 'DrumSolo', 'Acapella',
	'Euro-House', 'DanceHall', 'Goa', 'Drum&Bass', 'Club-House', 'Hardcore',
	'Terror', 'Indie', 'BritPop', 'Negerpunk', 'PolskPunk', 'Beat',
	'ChristianGangstaRap', 'HeavyMetal', 'BlackMetal', 'Crossover',
	'ContemporaryChristian', 'ChristianRock', 'Merengue', 'Salsa',
	'ThrashMetal', 'Anime', 'J-Pop', 'Synthpop', 'Rock/Pop', 'Unknown',
	'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown',
	'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown',
	'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown',
	'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown',
	'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown',
	'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown',
	'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown',
	'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown',
	'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown',
	'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown',
	'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown',
	'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown',
	'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown',
	'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown',
	'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown',
	'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown',
	'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown',
	'Unknown', 'Unknown', 'Unknown', 'Unknown'
)
"""The venerable ID3v1 genres"""

ID3V2_TEXT_ENCODING = { 0: 'latin_1', 1: 'utf_16', 2: 'utf_16_be', 3: 'utf_8' }
"""ID3v2 text encoding lookup table"""
ID3V2_TEXT_TERMS = { 0: b'\x00', 1: b'\x00\x00', 2: b'\x00\x00', 3: b'\x00' }
"""ID3v2 string terminating byte(s) table"""

def decode_synchsafe_int( i ):
	"""Decode SynchSafe integers from ID3v2 tags"""
	i = int.from_bytes( i, 'big' )
	if i & 0x80808080:
		raise Exception( 'Bad sync in SynchSafe integer!' )
	return ( ( i & 0xFF000000 ) >> 3 ) | ( ( i & 0x00FF0000 ) >> 2 ) | ( ( i & 0x0000FF00 ) >> 1 ) | ( i & 0x000000FF )

def encode_synchsafe_int( i ):
	"""Encode SynchSafe integers for ID3v2 tags"""
	return ( ( ( i & 0x0FE00000 ) << 3 ) | ( ( i & 0x001FC000 ) << 2 ) | ( ( i & 0x00003F80 ) << 1 ) | ( i & 0x0000007F ) ).to_bytes( 4, 'big' )

def read_id3v1( data ):
	"""Read ID3v1 tag if present and return the fields"""
	fields = dict()

	if len( data ) >= 128 and data[-128:-125] == b'TAG':
		if len( data ) >= 355 and data[-355:-351] == b'TAG+':
			titleLastSixty = data[-351:-291]
			artistLastSixty = data[-291:-231]
			albumLastSixty = data[-231:-171]
			genre = data[-170:-140].decode( 'ascii' ).rstrip( '\x00' )
		else:
			titleLastSixty = bytes()
			artistLastSixty = bytes()
			albumLastSixty = bytes()
			genre = str()

		title = ( data[-125:-95] + titleLastSixty ).decode( 'ascii' ).rstrip( ' \x00' )
		artist = ( data[-95:-65] + artistLastSixty ).decode( 'ascii' ).rstrip( ' \x00' )
		album = ( data[-65:-35] + albumLastSixty ).decode( 'ascii' ).rstrip( ' \x00' )
		year = data[-35:-31].decode( 'ascii' ).rstrip( ' \x00' )
		if data[-3] == 0:
			comment = data[-31:-3].decode( 'ascii' ).rstrip( ' \x00' )
			track = data[-2]
		elif data[-3] > 0x7F:
			comment = data[-31:-3].decode( 'ascii' ).rstrip( ' \x00' )
			track = 0
		else:
			comment = data[-31:-1].decode( 'ascii' ).rstrip( ' \x00' )
			track = 0
		if len( genre ) == 0:
			genre = ID3V1_GENRES[data[-1]]

		if len( title ) > 0:
			fields['title'] = title
		if len( artist ) > 0:
			fields['artist'] = artist
		if len( album ) > 0:
			fields['album'] = album
		if track > 0:
			fields['track'] = track
		if genre.upper() != 'UNKNOWN':
			fields['genre'] = genre
		if len( year ) > 0 and int( year ) > 0:
			fields['year'] = int( year )
		if len( comment ) > 0:
			fields['comment'] = comment

	return fields

def read_id3v2_data( data ):
	"""Read ID3v1 tag assuming it is present and return the fields"""
	assert len( data ) >= 10
	assert data[0:3] == b'ID3'
	assert data[3] == 2 or data[3] == 3 or data[3] == 4
	assert data[4] == 0

	fields = dict()

	if data[3] == 2:
		size = decode_synchsafe_int( data[6:10] ) + 10
		pos = 10

		while pos + 6 < size and data[pos] != 0:
			frame_size = int.from_bytes( data[pos+3:pos+6], 'big' )

			if data[pos:pos+3] == b'TT2':
				fields['title'] = data[pos+7:pos+6+frame_size].decode( ID3V2_TEXT_ENCODING[data[pos+6]] )
			elif data[pos:pos+3] == b'TP1':
				fields['artist'] = data[pos+7:pos+6+frame_size].decode( ID3V2_TEXT_ENCODING[data[pos+6]] )
			elif data[pos:pos+3] == b'TAL':
				fields['album'] = data[pos+7:pos+6+frame_size].decode( ID3V2_TEXT_ENCODING[data[pos+6]] )
			elif data[pos:pos+3] == b'TRK':
				fields['track'] = int( data[pos+7:pos+6+frame_size].decode( ID3V2_TEXT_ENCODING[data[pos+6]] ) )
			elif data[pos:pos+3] == b'TPA':
				fields['disc'] = int( data[pos+7:pos+6+frame_size].decode( ID3V2_TEXT_ENCODING[data[pos+6]] ) )
			elif data[pos:pos+3] == b'TCO':
				fields['genre'] = data[pos+7:pos+6+frame_size].decode( ID3V2_TEXT_ENCODING[data[pos+6]] )
			elif data[pos:pos+3] == b'TYE':
				fields['year'] = int( data[pos+7:pos+6+frame_size].decode( ID3V2_TEXT_ENCODING[data[pos+6]] ) )
			elif data[pos:pos+3] == b'COM':
				fields['comment'] = data[data.find( ID3V2_TEXT_TERMS[data[pos+6]], pos+10 ) + 1 : pos+10+frame_size].decode( ID3V2_TEXT_ENCODING[data[pos+6]] )
			elif data[pos:pos+3] == b'PIC':
				fields['cover'] = data[data.find( ID3V2_TEXT_TERMS[data[pos+6]], pos+11 ) + 1 : pos+10+frame_size]

			pos += frame_size + 6

	elif data[3] == 3 or data[3] == 4:
		size = decode_synchsafe_int( data[6:10] ) + 10
		if data[5] & 0x40:
			pos = 10 + decode_synchsafe_int( data[10:14] )
		else:
			pos = 10

		while pos + 10 <= size and data[pos] != 0:
			frame_size = int.from_bytes( data[pos+4:pos+8], 'big' )

			if data[pos:pos+4] == b'TIT2':
				fields['title'] = data[pos+11:pos+10+frame_size].decode( ID3V2_TEXT_ENCODING[data[pos+10]] )
			elif data[pos:pos+4] == b'TPE1':
				fields['artist'] = data[pos+11:pos+10+frame_size].decode( ID3V2_TEXT_ENCODING[data[pos+10]] )
			elif data[pos:pos+4] == b'TALB':
				fields['album'] = data[pos+11:pos+10+frame_size].decode( ID3V2_TEXT_ENCODING[data[pos+10]] )
			elif data[pos:pos+4] == b'TRCK':
				fields['track'] = int( data[pos+11:pos+10+frame_size].decode( ID3V2_TEXT_ENCODING[data[pos+10]] ) )
			elif data[pos:pos+4] == b'TPOS':
				fields['disc'] = int( data[pos+11:pos+10+frame_size].decode( ID3V2_TEXT_ENCODING[data[pos+10]] ) )
			elif data[pos:pos+4] == b'TCON':
				fields['genre'] = data[pos+11:pos+10+frame_size].decode( ID3V2_TEXT_ENCODING[data[pos+10]] )
				mat = re.match( '\((\d+)\)(\w+)', fields['genre'] )
				if mat and int( mat.group( 1 ) ) < 256 and ID3V1_GENRES[int( mat.group( 1 ) )] == mat.group( 2 ):
					fields['genre'] = mat.group( 2 )
			elif data[pos:pos+4] == b'TYER' or data[pos:pos+4] == b'TDRL' or data[pos:pos+4] == b'TDRC':
				fields['year'] = int( data[pos+11:pos+10+frame_size].decode( ID3V2_TEXT_ENCODING[data[pos+10]] ) )
			elif data[pos:pos+4] == b'COMM':
				fields['comment'] = data[data.find( ID3V2_TEXT_TERMS[data[pos+10]], pos+14 ) + len( ID3V2_TEXT_TERMS[data[pos+10]] ) : pos+10+frame_size].decode( ID3V2_TEXT_ENCODING[data[pos+10]] )
			elif data[pos:pos+4] == b'APIC':
				fields['cover'] = data[data.find( ID3V2_TEXT_TERMS[data[pos+10]], data.find( b'\x00', pos+11 ) + 2 ) + len( ID3V2_TEXT_TERMS[data[pos+10]] ) : pos+10+frame_size]
			elif data[pos:pos+4] == b'TDTG':
				fields['timestamp'] = data[pos+11:pos+10+frame_size].decode( ID3V2_TEXT_ENCODING[data[pos+10]] )

			pos += 10 + frame_size

	return fields

def read_id3v2_header( data ):
	"""Read IDv3 header if present and return the fields"""
	if len( data ) >= 10 and data[0:3] == b'ID3' and data[4] == 0:
		if data[3] == 2 or data[3] == 3:
			return read_id3v2_data( data[:10+decode_synchsafe_int( data[6:10] )] )
		elif data[3] == 4:
			if data[5] & 0x10:
				return read_id3v2_data( data[:20+decode_synchsafe_int( data[6:10] )] )
			else:
				return read_id3v2_data( data[:10+decode_synchsafe_int( data[6:10] )] )
	return dict()

def read_id3v2_footer( data ):
	"""Read IDv3 footer if present and return the fields"""
	pos = len( data ) - 10
	while pos > 0:
		if data[pos:pos+3] == b'ID3' and data[pos+4] == 0:
			if data[pos+3] == 2 or data[pos+3] == 3:
				return read_id3v2_data( data[pos:pos+10+decode_synchsafe_int( data[6:10] )] )
			elif data[pos+3] == 4:
				if data[5] & 0x10:
					return read_id3v2_data( data[pos:pos+20+decode_synchsafe_int( data[6:10] )] )
				else:
					return read_id3v2_data( data[pos:pos+10+decode_synchsafe_int( data[6:10] )] )
		pos -= 1
	return dict()

def remove_id3v1( data ):
	"""Remove ID3v1 tag if present"""
	if len( data ) >= 355:
		if data[-128:-125] == b'TAG':
			if data[-355:351] == b'TAG+':
				return data[0:-355]
			else:
				return data[0:-128]
	elif len( data ) >= 128:
		if data[-128:-125] == b'TAG':
			return data[0:-128]
	return data

def remove_id3v2_header( data ):
	"""Remove ID3v2 header tag if present"""
	if len( data ) >= 10 and data[0:3] == b'ID3' and data[4] == 0:
		if data[3] == 2 or data[3] == 3:
			return data[decode_synchsafe_int( data[6:10] )+10:]
		elif data[3] == 4:
			if data[5] & 0x10:
				return data[decode_synchsafe_int( data[6:10] )+20:]
			else:
				return data[decode_synchsafe_int( data[6:10] )+10:]
	return data

def remove_id3v2_footer( data ):
	"""Remove ID3v2 footer tag if present"""
	pos = len( data ) - 10
	while pos > 0:
		if data[pos:pos+3] == b'ID3' and data[pos+4] == 0:
			if data[pos+3] == 2 or data[pos+3] == 3:
				return data[:pos] + data[pos+decode_synchsafe_int( data[6:10] )+10:]
			elif data[pos+3] == 4:
				if data[pos+5] & 0x10:
					return data[:pos] + data[pos+decode_synchsafe_int( data[6:10] )+20:]
				else:
					return data[:pos] + data[pos+decode_synchsafe_int( data[6:10] )+10:]
		pos -= 1
	return data

def write_id3v2_header( data, fields ):
	"""Add an ID3v2 header to the data assuming none already present"""
	body = bytes()

	if 'title' in fields:
		title_bytes = b'\x03' + fields['title'].encode( 'utf_8' )
		body += b'TIT2' + len( title_bytes ).to_bytes( 4, 'big' ) + b'\x00\x00' + title_bytes
	if 'artist' in fields:
		artist_bytes = b'\x03' + fields['artist'].encode( 'utf_8' )
		body += b'TPE1' + len( artist_bytes ).to_bytes( 4, 'big' ) + b'\x00\x00' + artist_bytes
	if 'album' in fields:
		album_bytes = b'\x03' + fields['album'].encode( 'utf_8' )
		body += b'TALB' + len( album_bytes ).to_bytes( 4, 'big' ) + b'\x00\x00' + album_bytes
	if 'track' in fields:
		track_bytes = b'\x00' + str( fields['track'] ).encode( 'latin_1' )
		body += b'TRCK' + len( track_bytes ).to_bytes( 4, 'big' ) + b'\x00\x00' + track_bytes
	if 'disc' in fields:
		disc_bytes = b'\x00' + str( fields['disc'] ).encode( 'latin_1' )
		body += b'TPOS' + len( disc_bytes ).to_bytes( 4, 'big' ) + b'\x00\x00' + disc_bytes
	if 'genre' in fields:
		genre_bytes = b'\x03' + fields['genre'].encode( 'utf_8' )
		body += b'TCON' + len( genre_bytes ).to_bytes( 4, 'big' ) + b'\x00\x00' + genre_bytes
	if 'year' in fields:
		year_bytes = b'\x00' + str( fields['year'] ).encode( 'latin_1' )
		body += b'TYER' + len( year_bytes ).to_bytes( 4, 'big' ) + b'\x00\x00' + year_bytes
	if 'comment' in fields:
		comment_bytes = b'\x03   \x00' + fields['comment'].encode( 'utf_8' )
		body += b'COMM' + len( comment_bytes ).to_bytes( 4, 'big' ) + b'\x00\x00' + comment_bytes
	if 'cover' in fields:
		cover_bytes = b'\x00' + ( 'image/' + imghdr.what( '', h=fields['cover'] ) ).encode( 'latin_1' ) + b'\x00\x03\x00' + fields['cover']
		body += b'APIC' + len( cover_bytes ).to_bytes( 4, 'big' ) + b'\x00\x00' + cover_bytes
	fields['timestamp'] = datetime.datetime.utcnow().replace( microsecond=0 ).isoformat()
	timestamp_bytes = b'\x00' + fields['timestamp'].encode( 'latin_1' )
	body += b'TDTG' + len( timestamp_bytes ).to_bytes( 4, 'big' ) + b'\x00\x00' + timestamp_bytes

	return b'ID3\x04\x00\x00' + encode_synchsafe_int( len( body ) ) + body + data

def main( argv=None ):
	# Parse command line
	command_line_parser = argparse.ArgumentParser( description='MP3 ID3 tag viewer/editor' )
	command_line_parser.add_argument( '-r', '--discard', action='store_true', help='discard existing tag data' )
	#command_line_parser.add_argument( '-n', '--rename', help='rename file using PATTERN', metavar='PATTERN' )
	command_line_parser.add_argument( '-t', '--title', help='set title field', metavar='STRING' )
	command_line_parser.add_argument( '-a', '--artist', help='set artist field', metavar='STRING' )
	command_line_parser.add_argument( '-A', '--album', help='set album field', metavar='STRING' )
	command_line_parser.add_argument( '-T', '--track', type=int, help='set track number field', metavar='INT' )
	command_line_parser.add_argument( '-D', '--disc', type=int, help='set disc number field', metavar='INT' )
	command_line_parser.add_argument( '-g', '--genre', help='set genre field', metavar='STRING' )
	command_line_parser.add_argument( '-y', '--year', type=int, help='set year field', metavar='INT' )
	command_line_parser.add_argument( '-c', '--comment', help='set comment field', metavar='STRING' )
	command_line_parser.add_argument( '-C', '--cover', help='set cover art field', metavar='FILE' )
	command_line_parser.add_argument( '-E', '--export-cover', help='export cover art', metavar='FILE' )
	command_line_parser.add_argument( '-R', '--remove-cover', action='store_true', help='remove cover art' )
	command_line_parser.add_argument( '-f', '--check-footer', action='store_true', help='check for an ID3v2 footer' )
	command_line_parser.add_argument( 'inputs', nargs='+', help='file(s) to view or edit', metavar='INPUT' )

	if argv is None:
		command_line = command_line_parser.parse_args()
	else:
		command_line = command_line_parser.parse_args( argv )

	# Collect tag fields
	new_tag = dict()
	if command_line.title is not None:
		new_tag['title'] = command_line.title
	if command_line.artist is not None:
		new_tag['artist'] = command_line.artist
	if command_line.album is not None:
		new_tag['album'] = command_line.album
	if command_line.track is not None:
		new_tag['track'] = command_line.track
	if command_line.disc is not None:
		new_tag['disc'] = command_line.disc
	if command_line.genre is not None:
		new_tag['genre'] = command_line.genre
	if command_line.year is not None:
		new_tag['year'] = command_line.year
	if command_line.comment is not None:
		new_tag['comment'] = command_line.comment
	if command_line.cover is not None:
		with open( command_line.cover, 'rb' ) as c:
			new_tag['cover'] = c.read()

	# Process inputs
	for i in command_line.inputs:
		with open( i, 'rb' ) as f:
			data = f.read()

		# Get old tag
		tag = dict()
		if not command_line.discard:
			tag.update( read_id3v1( data ) )
			if command_line.check_footer:
				tag.update( read_id3v2_footer( data ) )
			tag.update( read_id3v2_header( data ) )

		# Remove old tag
		if len( new_tag ) > 0 or command_line.remove_cover:
			data = remove_id3v1( data )
			if command_line.check_footer:
				data = remove_id3v2_footer( data )
			data = remove_id3v2_header( data )

		# Export cover
		if command_line.export_cover is not None:
			with open( command_line.export_cover, 'wb' ) as f:
				f.write( tag['cover'] )

		# Remove cover
		if command_line.remove_cover:
			del tag['cover']

		# Insert new tag
		if len( new_tag ) > 0:
			tag.update( new_tag )

		# Delete empty fields
		if 'title' in tag and len( tag['title'] ) == 0:
			del tag['title']
		if 'artist' in tag and len( tag['artist'] ) == 0:
			del tag['artist']
		if 'album' in tag and len( tag['album'] ) == 0:
			del tag['album']
		if 'track' in tag and tag['track'] == 0:
			del tag['track']
		if 'disc' in tag and tag['disc'] == 0:
			del tag['disc']
		if 'genre' in tag and len( tag['genre'] ) == 0:
			del tag['genre']
		if 'year' in tag and tag['year'] == 0:
			del tag['year']
		if 'comment' in tag and len( tag['comment'] ) == 0:
			del tag['comment']
		if 'cover' in tag and len( tag['cover'] ) == 0:
			del tag['cover']

		# Update file
		if len( new_tag ) > 0 or command_line.remove_cover:
			data = write_id3v2_header( data, tag )
			with open( i, 'wb' ) as f:
				f.write( data )

		# Print tag
		print( 'Filename:\t', os.path.basename( i ), sep=str() )
		if 'title' in tag:
			print( 'Title:\t\t', tag['title'], sep=str() )
		if 'artist' in tas:
			print( 'Artist:\t\t', tag['artist'], sep=str() )
		if 'track' in tag:
			print( 'Track#:\t\t', tag['track'], sep=str() )
		if 'disc' in tag:
			print( 'Disc#:\t\t', tag['disc'], sep=str() )
		if 'genre' in tag:
			print( 'Genre:\t\t', tag['genre'], sep=str() )
		if 'year' in tag:
			print( 'Year:\t\t', tag['year'], sep=str() )
		if 'comment' in tag:
			print( 'Comment:\t\t', tag['comment'], sep=str() )
		if 'timestamp' in tag:
			print( 'Timestamp:\t', tag['timestamp'], sep=str() )
		print( 'Cover:\t\t', 'cover' in tag, sep=str() )
		print()

	# Done!
	return 0

if __name__ == '__main__':
	sys.exit( main() )
