#!/usr/bin/perl
use Bio::SearchIO;
use Getopt::Long;
use Switch;

my $input;
my $identity = 0;
my $positives = 0;
my $align_percent = 0;
my $n = 5;
my $out_type = "Sid";
my $help;

GetOptions("f=s"=>\$input,
            "i=s"=>\$identity,
            "p=s"=>\$positives,
            "c=s"=>\$align_percent,
            "n=s"=>\$n,
            "t=s"=>\$out_type,
            "h!"=>\$help,
    );

if ($help) {
    &Usage;
}


unless ($input) {
    &Usage;
}

# print the header of output;
print "Query\tSubject\tIdentity\tAlignment_length\tMismatches\tGaps\tQ.start\tQ.end\tS.start\tS.end\tE-value\tScore\n";

my $obj = Bio::SearchIO->new(-format=>'blast',-file=>$input);
while (my $r = $obj->next_result) {
    my $i = 0;
    while (my $hit = $r->next_hit and $i<$n) {
        my $qname = $r->query_name;
        my $hname = $hit->name;
        my $desc = $hit->description;
        my $hit_length = $hit->length;
        my ($percentid, $frac_cons, $aln_length, $mismatch, $gap_num, $q_star, $q_end, $s_star, $s_end, $evalue, $score);
        if (my $hsp = $hit->hsp) {
            $percentid = sprintf("%.2f", $hsp->percent_identity());  # hsp identity;
            $frac_cons = ($hsp->frac_conserved('total'))*100;       # hsp positives;
            $aln_length = $hsp->length('total');
            my $coverage = $aln_length/$hit_length*100;      # hsp coverage with hit;
            $mismatch = scalar($hsp->seq_inds('hit', 'mismatch'));
            $gap_num = $hsp->gaps('total');
            ($q_star, $q_end) = $hsp->range('query');
            ($s_star, $s_end) = $hsp->range('sbjct');
            my $strand = $hsp->strand('sbjct');
            if ($strand == -1) {
                my $i = $s_star;
                $s_star = $s_end;
                $s_end = $i;
            }
            $evalue = $hsp->evalue();
            $score = $hsp->bits();
#            $score = $hsp->score();
            if ($percentid >= $identity && $frac_cons >= $positives && $coverage >= $align_percent) {
                switch ($out_type) {
                    case "Sdesc" {$desc = &desc_cut($desc); print "$qname\t$desc\t$percentid\t$aln_length\t$mismatch\t$gap_num\t$q_star\t$q_end\t$s_star\t$s_end\t$evalue\t$score\n";}
                    case "VF" {$desc =~ s/\s*$//; print "$qname\t$desc\t$percentid\t$aln_length\t$mismatch\t$gap_num\t$q_star\t$q_end\t$s_star\t$s_end\t$evalue\t$score\n";}
                    #case "VF" {$desc =~ s/\[[^\[\]]*?\]\s*$//; print "$qname\t$desc\t$percentid\t$aln_length\t$mismatch\t$gap_num\t$q_star\t$q_end\t$s_star\t$s_end\t$evalue\t$score\n";}
                    case "nr" {
                        $desc = &desc_cut($desc); 
                        $desc = $hname . ' ' . $desc; 
                        print "$qname\t$desc\t$percentid\t$aln_length\t$mismatch\t$gap_num\t$q_star\t$q_end\t$s_star\t$s_end\t$evalue\t$score\n";
                    }
                    else  {print "$qname\t$hname\t$percentid\t$aln_length\t$mismatch\t$gap_num\t$q_star\t$q_end\t$s_star\t$s_end\t$evalue\t$score\n";}
                }
            }
        }
        $i++;
    }
}


# ----------------------------------------------------------------
sub desc_cut {
    my $desc = shift @_;
    my $str;
    if ($desc =~ /RecName\: Full\=(.*?)(\[|;|$)/){
        $str = $1;
    } elsif ($desc=~/Full=(.*?)(\[|;|$|sp\|)/) {
        $str = $1;
    } elsif ($desc=~/MULTISPECIES\: (.*?)\s*(\[|>?gi\||sp\||&)/) {
        $str = $1;
    } elsif ($desc=~/(.*?)\s*(\[|>?gi\||sp\||&)/) {
        $str = $1;
    } else {
        $str = $desc;
    }
    $str =~ s/.*$//;
    $str;
}

sub Usage {
    die<<"EOF";
    Usage:
        perl $0 -n 5 -f [blast_result] > output

    Options:
        -f blastFile  blast result(outfmt is 0) as input
        -i [0-100]    filter the blast result by identity, defaults not filtered.
        -p [0-100]    filter the blast result by positives, defaults not filtered.
        -c [0-100]    filter the blast result by alignment region percent, defaults not filtered.
        -n [int]      number of alignment, defaults 5
        -t [str]      outfmt type for some database. ('nr', 'VF', 'AR', 'Sid', 'Sdesc'). defaults is "Sid". 
                      "Sid" for print Subject id instead of desc; "Sdesc" for print Subject description instead of id; "nr" for nr database; "VF" for VFDB; "AR" for ARDB.
        -h            print usage for this script;
EOF
}
