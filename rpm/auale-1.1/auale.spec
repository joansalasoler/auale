Name:             auale
Version:          1.1.0
Release:          1%{?dist}
Summary:          Play oware abapa against the computer or annotate your games
Packager:	      Joan Sala Soler <contact@joansala.com>
Group:            Amusements/Games
License:          GPLv3+
URL:              http://www.joansala.com/auale/
Source0:          %{name}-%{version}.tar.gz

BuildArch:        noarch
BuildRoot:        %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:    python2-devel
BuildRequires:    python-setuptools

Requires(post):   desktop-file-utils
Requires(postun): desktop-file-utils

Requires:         python >= 2.6
Requires:         gtk3 >= 3.10
Requires:         jre >= 1.6

%if %{defined fedora}
Requires:         pygobject3 >= 3.8
Requires:         pycairo
%endif

%if 0%{?suse_version}
Requires:         python-gobject >= 3.8
Requires:         python-gobject-cairo >= 3.8
Requires:         python-cairo
Requires:         typelib-1_0-Gtk-3_0
%endif

%if 0%{?suse_version} > 1000
Suggests:         SDL2
Suggests:         SDL2_mixer
%endif


%description
Aualé is a graphical user interface for the popular Oware Abapa board game. It
may be used to analyze, record and share your own mancala games or to play
against the computer.

This interface communicates with an oware engine through an adapted version of
the Universal Chess Interface protocol, which makes it suitable for use with
multiple mancala playing programs. Although, currently only the Aalina game
engine supports this protocol.

Some of its main features include:

 * Play against the computer or watch how it plays.
 * Easily configurable computer strength.
 * Annotate your matches with an easy to use interface.
 * Save your games using a portable format which resembles that of the
   popular Portable Game Notation format.


%prep
%setup -q


%build
cd %{_builddir}/%{name}-%{version}/src/%{name}
%{__python} setup.py build


%install
rm -rf %{buildroot}

cd %{_builddir}/%{name}-%{version}/src/%{name}
%{__python} setup.py install --skip-build --root=%{buildroot} \
    --install-lib=%{_datadir}/%{name}

cp -R %{_builddir}/%{name}-%{version}/res/share %{buildroot}/%{_prefix}

mkdir -p %{buildroot}/%{_bindir}
chmod 755 %{buildroot}/%{_datadir}/%{name}/__main__.py
ln -s ../share/%{name}/__main__.py %{buildroot}/%{_bindir}/%{name}


%clean
rm -rf %{buildroot}


%files
%defattr(-,root,root,-)
%doc AUTHORS COPYING NEWS README
%{_bindir}/%{name}
%{_datadir}/*


%post
if which gtk-update-icon-cache >/dev/null 2>&1 ; then
    gtk-update-icon-cache %{_datadir}/icons/%{name}.png
fi

if which update-mime-database >/dev/null 2>&1 ; then
    update-mime-database %{_datadir}/mime
fi

if update-desktop-database >/dev/null 2>&1 ; then
    update-desktop-database
fi

glib-compile-schemas %{_datadir}/glib-2.0/schemas


%postun
if which gtk-update-icon-cache >/dev/null 2>&1 ; then
    gtk-update-icon-cache /usr/share/icons/%{name}.png
fi

if which update-mime-database >/dev/null 2>&1 ; then
    update-mime-database %{_datadir}/mime
fi

if update-desktop-database >/dev/null 2>&1 ; then
    update-desktop-database
fi

glib-compile-schemas %{_datadir}/glib-2.0/schemas


%changelog
