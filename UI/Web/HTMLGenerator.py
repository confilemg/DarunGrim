import sys
TestDir =  r'..\..\Bin Collector'
sys.path.append( TestDir )
sys.path.append(r'..\..\Diff Inspector')
import os
import PatchDatabaseWrapper
import PatchTimeline
import DarunGrimSessions
import DarunGrimDatabaseWrapper
import DarunGrimAnalyzers

from mako.template import Template

HeadText = """
<link rel="stylesheet" type="text/css" href="/data/jquery-ui.css" media="screen" />
<script type="text/javascript" src="/data/jquery-ui.min.js"></script>
<script type="text/javascript" src="/data/tablesorter/jquery-latest.js"></script> 
<script type="text/javascript" src="/data/tablesorter/jquery.tablesorter.js"></script> 
<link rel="stylesheet" href="/data/themes/basic/style.css" type="text/css" media="print, projection, screen" />
	
<script type="text/javascript">
	$(document).ready(function() 
		{ 
			$("#mainTable").tablesorter( {sortList:[[0,0],[2,1]], widgets: ['zebra']} ); 
		} 
	); 
</script>
"""

PatchesTemplateText = """<%def name="layoutdata(somedata)">
	<table class="Table">
	% for item in somedata:
		<tr>
			<td><a href="PatchInfo?id=${item.id}">${item.name}</a></td>
			<td>${item.title}</td>
		</tr>
	% endfor
	</table>
</%def>
<html>
""" + HeadText + """
<body>
<div id=Content>
<%self:layoutdata somedata="${patches}" args="col">\
</%self:layoutdata>
</div>
</body>
</html>"""

PatchInfoTemplateText = """<%def name="layoutdata(somedata)">
<p><a href="/">List</a>
	<table class="Table">
	% for item in somedata:
		<tr>
			<td><a href="DownloadInfo?patch_id=${id}&id=${item.id}">${item.label}</a></td>
			<td>${item.filename}</td>
		</tr>
	% endfor
	</table>
</%def>
<html>
""" + HeadText + """
<body>
<div id=Content>
<%self:layoutdata somedata="${downloads}" args="col">\
</%self:layoutdata>
</div>
</body>
</html>"""

DownloadInfoTemplateText = """<%def name="layoutdata(somedata)">
<p><a href="/">List</a>
&gt;<a href="PatchInfo?id=${patch_id}">Patch</a>
	<table class="Table">
	% for item in somedata:
		<tr>
			<td><a href="FileInfo?patch_id=${patch_id}&download_id=${id}&id=${item.id}">${item.filename}</a></td>
			<td>${item.version_string}</td>
		</tr>
	% endfor
	</table>
</%def>
<html>
""" + HeadText + """
<body>
<div id=Content>
<%self:layoutdata somedata="${files}" args="col">\
</%self:layoutdata>
</div>
</body>
</html>"""

FileInfoTemplateText = """<%def name="layoutdata(somedata)">
<p><a href="/">List</a>
&gt;<a href="PatchInfo?id=${patch_id}">Patch</a>
&gt;<a href="DownloadInfo?patch_id=${patch_id}&id=${download_id}">Systems</a>
	<table class="Table">
		<tr>
			<td>Company Name</td>
			<td>${somedata.company_name}</td>
		</tr>
		<tr>
			<td>Operating System</td>
			<td>${somedata.operating_system}</td>
		</tr>
		<tr>
			<td>Service Pack</td>
			<td>${somedata.service_pack}</td>
		</tr>
		<tr>
			<td>Filename</td>
			<td>${somedata.filename}</td>
		</tr>
		<tr>
			<td>Unpatched Filename</td>
			<td>${source_patch_name}: ${source_filename}</td>
		</tr>
		<tr>
			<td>Patched Filename</td>
			<td>${target_patch_name}: ${target_filename}</td>
		</tr>
	</table>
</%def>
<html>
""" + HeadText + """
<body>
<div id=Content>
<%self:layoutdata somedata="${file_index_entry}" args="col">\
</%self:layoutdata>
<form name="input" action="StartDiff" method="get">
<input type="hidden" name="patch_id" value="${patch_id}"/>
<input type="hidden" name="download_id" value="${download_id}"/>
<input type="hidden" name="file_id" value="${id}"/>
<input type="hidden" name="source_id" value="${source_id}"/>
<input type="hidden" name="target_id" value="${target_id}"/>
<input type="submit" value="Start Diffing" />
</form> 
</div>
</body>
</html>"""

DiffInfoTemplateText = """<%def name="layoutdata(somedata)">
<META HTTP-EQUIV="Refresh" CONTENT="1; URL="ShowFunctionMatchInfo?source_id=${source_id}&target_id=${target_id}">
<p><a href="ShowFunctionMatchInfo?databasename=source_id=${source_id}&target_id=${target_id}">Show Function Match Table</a>
</%def>
<html>
""" + HeadText + """
<body>
<div id=Content>
<%self:layoutdata somedata="${file_index_entry}" args="col">\
</%self:layoutdata>
</div>
</body>
</html>"""

FunctionmatchInfosTemplateText = """<%def name="layoutdata(function_match_infos)">
<p><a href="/">List</a>
&gt;<a href="PatchInfo?id=${patch_id}">Patch</a>
&gt;<a href="DownloadInfo?patch_id=${patch_id}&id=${download_id}">Systems</a>
&gt;<a href="FileInfo?patch_id=${patch_id}&download_id=${download_id}&id=${file_id}">Files</a>
	<table id="mainTable" class="tablesorter">
		<thead>
		<tr>
			<th>Unpatched</th>
			<th>Address</th>
			<th>Unidentified</th>
			<th>Patched</th>
			<th>Address</th>
			<th>Unidentified</th>
			<th>Matched</th>
			<th>Modifications</th>
			<th>Security Implication Score</th>
			<th>Operations</th>
		</tr>
		</thead>

		<tbody>
		% for ( function_match_info, security_implication_score ) in function_match_infos:
			<tr>
				<td>${function_match_info.source_function_name}</td>
				<td>${hex(function_match_info.source_address)[2:].upper()}</td>
				<td>${function_match_info.non_match_count_for_the_source}</td>
				<td>${function_match_info.target_function_name}</td>
				<td>${hex(function_match_info.target_address)[2:].upper()}</td>
				<td>${function_match_info.non_match_count_for_the_target}</td>
				<td>${function_match_info.match_count_for_the_source}</td>
				<td>${function_match_info.match_count_with_modificationfor_the_source}</td>
				<td>${'%d' % ( security_implication_score) }</td>
				<td><a href="ShowBasicBlockMatchInfo?patch_id=${patch_id}&download_id=${download_id}&file_id=${file_id}&source_id=${source_id}&target_id=${target_id}&source_address=${function_match_info.source_address}&target_address=${function_match_info.target_address}">Show</a></td>
			</tr>
		% endfor
		</tbody>
	</table>
</%def>
<html>
""" + HeadText + """

<body>
<div id=Content>
<%self:layoutdata function_match_infos="${function_match_infos}" args="col">\
</%self:layoutdata>
</div>
</body>
</html>"""

"""
str(function_match_info.block_type)
str(function_match_info.type)
str( function_match_info.match_rate )
"""


ComparisonTableTemplateText = """<%def name="layoutdata(source_function_name, target_function_name, comparison_table)">
<p><a href="/">List</a>
&gt;<a href="PatchInfo?id=${patch_id}">Patch</a>
&gt;<a href="DownloadInfo?patch_id=${patch_id}&id=${download_id}">Systems</a>
&gt;<a href="FileInfo?patch_id=${patch_id}&download_id=${download_id}&id=${file_id}">Files</a>
&gt;<a href="ShowFunctionMatchInfo?patch_id=${patch_id}&download_id=${download_id}&file_id=${file_id}&source_id=${source_id}&target_id=${target_id}">Functions</a>

	<table class="Block">
		<tr>
			% if source_function_name:
				<td><b>Unpatched: ${source_function_name}<b></td>
			% else:
				<td><b>Unpatched</b></td>
			% endif
			% if target_function_name:
				<td><b>Patched: ${target_function_name}<b></td>
			% else:
				<td><b>Patched</b></td>
			% endif
		</tr>
	% for ( left_address, left_lines, right_address, right_lines, match_rate ) in comparison_table:
		% if left_address != 0 or right_address != 0:
			<tr>
				% if right_address == 0:
					<td class="UnidentifiedBlock">
				% else:
					% if match_rate == 100 or left_address == 0:
						<td class="MatchedBlock">
					% else:
						<td class="ModifiedBlock">
					% endif
				% endif
				% if left_address != 0:
					<b>[${hex(left_address)[2:].upper()}]</b>
				% endif
				<p>${left_lines}</td>
	
				% if left_address == 0:
					<td class="UnidentifiedBlock">
				% else:
					% if match_rate == 100 or right_address == 0:
						<td class="MatchedBlock">
					% else:
						<td class="ModifiedBlock">
					% endif
				% endif
				% if right_address != 0:
					<b>[${hex(right_address)[2:].upper()}]</b>
				% endif
				<p>${right_lines}</td>
			</tr>
		% endif
	% endfor
	</table>
</%def>
""" + HeadText + """
<div id=Content>
<%self:layoutdata source_function_name="${source_function_name}" target_function_name="${target_function_name}" comparison_table="${comparison_table}" args="col">\
</%self:layoutdata>
</div>
</div>
"""

class Worker:
	def __init__ ( self, database = os.path.join( TestDir, 'test.db' ) ):
		self.DatabaseName = database
		self.Database = PatchDatabaseWrapper.Database( self.DatabaseName )
		self.PatchTimelineAnalyzer = PatchTimeline.Analyzer( database = self.Database )
		
		self.DGFDirectory = r'C:\mat\Projects\DGFs'
		self.FileDiffer = DarunGrimSessions.Manager( self.DatabaseName, self.DGFDirectory )
		self.PatternAnalyzer = DarunGrimAnalyzers.PatternAnalyzer()

	def Patches( self ):
		mytemplate = Template( PatchesTemplateText )
		patches = self.Database.GetPatches()
		return mytemplate.render( patches=patches )

	def PatchInfo( self, id ):
		mytemplate = Template( PatchInfoTemplateText )
		downloads = self.Database.GetDownloadByPatchID( id )
		return mytemplate.render( id=id, downloads=downloads )
	
	def DownloadInfo( self, patch_id, id ):
		mytemplate = Template( DownloadInfoTemplateText )
		files = self.Database.GetFileByDownloadID( id )
		return mytemplate.render( patch_id=patch_id, id=id, files=files )

	def FileInfo( self, patch_id, download_id, id ):
		#PatchTimeline
		[ file_index_entry ] = self.Database.GetFileByID( id )
		filename = file_index_entry.filename
		target_patch_name = file_index_entry.downloads.patches.name

		source_id = 0
		source_patch_name = 'Not Found'
		source_filename = 'Not Found'
		target_filename = 'Not Found'
		target_id = 0
		for ( target_patch_name, target_file_entry, source_patch_name, source_file_entry ) in self.PatchTimelineAnalyzer.GetPatchPairsForAnalysis( filename = filename, id = id, patch_name = target_patch_name ):
			print '='*80
			print target_patch_name,source_patch_name

			source_filename = source_file_entry['full_path']
			source_id = source_file_entry['id']

			target_filename = target_file_entry['full_path']
			target_id = target_file_entry['id']

		mytemplate = Template( FileInfoTemplateText )
		return mytemplate.render(
			patch_id = patch_id,
			download_id = download_id,
			id = id,
			file_index_entry=file_index_entry, 
			source_patch_name = source_patch_name, 
			source_filename = source_filename,
			source_id = source_id,
			target_patch_name = target_patch_name, 
			target_filename = target_filename,
			target_id = target_id
		)

	def GenerateDGFName( self, source_id, target_id ):
		return os.path.join( self.DGFDirectory, str( source_id ) + '_' + str( target_id ) + '.dgf')

	def StartDiff( self, patch_id, download_id, file_id, source_id, target_id ):
		print 'StartDiff', source_id,target_id
		databasename = self.GenerateDGFName( source_id, target_id )
		self.FileDiffer.InitFileDiffByID( source_id, target_id, databasename )
		print 'StartDiff: ', source_id,'/',target_id,'/', databasename
		#mytemplate = Template( DiffInfoTemplateText )
		#return mytemplate.render( databasename = databasename )
		return self.GetFunctionMatchInfo( patch_id, download_id, file_id, source_id=source_id, target_id = target_id )

	def GetFunctionMatchInfo( self, patch_id, download_id, file_id, source_id, target_id ):
		databasename = self.GenerateDGFName( source_id, target_id )
		database = DarunGrimDatabaseWrapper.Database( databasename )
		function_match_infos = []
		for function_match_info in database.GetFunctionMatchInfo():
			if function_match_info.non_match_count_for_the_source > 0 or \
				function_match_info.non_match_count_for_the_target > 0 or \
				function_match_info.match_count_with_modificationfor_the_source > 0:

				databasename = self.GenerateDGFName( source_id, target_id )
				security_implications_score = self.PatternAnalyzer.GetSecurityImplicationsScore( 
											databasename,
											function_match_info.source_address, 
											function_match_info.target_address )

				function_match_infos.append( ( function_match_info, security_implications_score ) )
				
		mytemplate = Template( FunctionmatchInfosTemplateText )
		return mytemplate.render(  patch_id=patch_id, download_id = download_id, file_id = file_id, source_id=source_id, target_id = target_id, function_match_infos = function_match_infos )

	def GetDisasmComparisonTextByFunctionAddress( self, patch_id, download_id, file_id, source_id, target_id, source_address, target_address, source_function_name = None, target_function_name = None ):
		databasename = self.GenerateDGFName( source_id, target_id )
		database = DarunGrimDatabaseWrapper.Database( databasename )
		
		source_address = int(source_address)
		target_address = int(target_address)

		if not source_function_name:
			source_function_name = database.GetBlockName( 1, source_address )

		if not target_function_name:
			target_function_name = database.GetBlockName( 2, target_address )

		print 'source_function_name', source_function_name
		print 'target_function_name', target_function_name
		
		comparison_table = database.GetDisasmComparisonTextByFunctionAddress( source_address, target_address )
		text_comparison_table = []

		left_line_security_implications_score_total = 0
		right_line_security_implications_score_total = 0
		for ( left_address, left_lines, right_address, right_lines, match_rate ) in comparison_table:
			left_line_security_implications_score = 0
			right_line_security_implications_score = 0
			if (right_address == 0 and left_address !=0) or match_rate < 100 :
				( left_line_security_implications_score, left_line_text ) = self.PatternAnalyzer.GetDisasmLinesWithSecurityImplications( left_lines )
			else:
				left_line_text = "<p>".join( left_lines )

			if (left_address == 0 and right_address !=0) or match_rate < 100 :
				( right_line_security_implications_score, right_line_text ) = self.PatternAnalyzer.GetDisasmLinesWithSecurityImplications( right_lines )
			else:
				right_line_text = "<p>".join( right_lines )

			left_line_security_implications_score_total += left_line_security_implications_score
			right_line_security_implications_score_total += right_line_security_implications_score
			text_comparison_table.append(( left_address, left_line_text, right_address, right_line_text, match_rate ) )

		mytemplate = Template( ComparisonTableTemplateText )
		return mytemplate.render( source_function_name = source_function_name, 
									target_function_name = target_function_name,
									comparison_table = text_comparison_table, 
									source_id = source_id, 
									target_id = target_id, 
									patch_id=patch_id, 
									download_id=download_id, 
									file_id=file_id
						)

	def GetDisasmComparisonText( self, source_id, target_id ):
		databasename = self.GenerateDGFName( source_id, target_id )
		database = DarunGrimDatabaseWrapper.Database( databasename )
		function_match_infos = []
		ret = ''
		for function_match_info in database.GetFunctionMatchInfo():
			if function_match_info.non_match_count_for_the_source > 0 or function_match_info.non_match_count_for_the_target > 0:
				ret += worker.GetDisasmComparisonTextByFunctionAddress( databasename, 
					function_match_info.source_address, 
					function_match_info.target_address,
					source_function_name = function_match_info.source_function_name,
					target_function_name = function_match_info.target_function_name
				) 
		return ret

if __name__ == '__main__':
	worker = Worker()
	#print worker.Patches()
	databasename = r'..\..\Diff Inspector\Samples\MS06-040-MS04-022-netapi32.dgf'
	#print worker.GetFunctionMatchInfo( databasename )
	#print worker.GetDisasmComparisonTextByFunctionAddress( databasename, 0x71c21d00, 0x5b870058 )
	#print worker.GetDisasmComparisonTextByFunctionAddress( databasename, 0x71c40a4a,0x5b893ab1 )  
	print worker.GetDisasmComparisonText( databasename )